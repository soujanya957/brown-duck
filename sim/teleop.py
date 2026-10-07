"""Keyboard teleop for Open Duck Mini v2 in MuJoCo (no GPU or training-framework deps).

Vendored and merged from apirrone/Open_Duck_Playground:
  - playground/open_duck_mini_v2/mujoco_infer_base.py  (MJInferBase)
  - playground/open_duck_mini_v2/mujoco_infer.py       (MjInfer)
Changes vs upstream:
  - the model is loaded with mujoco.MjModel.from_xml_path instead of the upstream asset loader
  - the unused LowPassActionFilter is removed
  - new key bindings (see CONTROLS), command printing, --save_obs is opt-in
  - default paths are relative to this file
Observation, action scale, reference-motion phase and motor speed limits are unchanged.

Run:  mjpython sim/teleop.py   (macOS)
      python sim/teleop.py     (Linux / Windows)
"""

import argparse
import pickle
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

from onnx_infer import OnnxInfer
from poly_reference_motion_numpy import PolyReferenceMotion

HERE = Path(__file__).resolve().parent

USE_MOTOR_SPEED_LIMITS = True

# Joint order the policy was trained with. Checked at startup.
EXPECTED_ACTUATORS = [
    "left_hip_yaw",
    "left_hip_roll",
    "left_hip_pitch",
    "left_knee",
    "left_ankle",
    "neck_pitch",
    "head_pitch",
    "head_yaw",
    "head_roll",
    "right_hip_yaw",
    "right_hip_roll",
    "right_hip_pitch",
    "right_knee",
    "right_ankle",
]


class MJInferBase:
    def __init__(self, model_path):

        self.model = mujoco.MjModel.from_xml_path(str(model_path))
        print(model_path)

        self.sim_dt = 0.002
        self.decimation = 10
        self.model.opt.timestep = self.sim_dt
        self.data = mujoco.MjData(self.model)
        mujoco.mj_step(self.model, self.data)

        self.num_dofs = self.model.nu
        self.floating_base_name = [
            self.model.jnt(k).name
            for k in range(0, self.model.njnt)
            if self.model.jnt(k).type == 0
        ][
            0
        ]  # assuming only one floating object!
        self.actuator_names = [
            self.model.actuator(k).name for k in range(0, self.model.nu)
        ]  # will be useful to get only the actuators we care about
        self.joint_names = [  # njnt = all joints (including floating base, actuators and backlash joints)
            self.model.jnt(k).name for k in range(0, self.model.njnt)
        ]  # all the joint (including the backlash joints)
        self.backlash_joint_names = [
            j
            for j in self.joint_names
            if j not in self.actuator_names and j not in self.floating_base_name
        ]  # only the dummy backlash joint
        self.all_joint_ids = [self.get_joint_id_from_name(n) for n in self.joint_names]
        self.all_joint_qpos_addr = [
            self.get_joint_addr_from_name(n) for n in self.joint_names
        ]

        self.actuator_joint_ids = [
            self.get_joint_id_from_name(n) for n in self.actuator_names
        ]
        self.actuator_joint_qpos_addr = [
            self.get_joint_addr_from_name(n) for n in self.actuator_names
        ]

        self.backlash_joint_ids = [
            self.get_joint_id_from_name(n) for n in self.backlash_joint_names
        ]

        self.backlash_joint_qpos_addr = [
            self.get_joint_addr_from_name(n) for n in self.backlash_joint_names
        ]

        self.all_qvel_addr = np.array(
            [self.model.jnt_dofadr[jad] for jad in self.all_joint_ids]
        )
        self.actuator_qvel_addr = np.array(
            [self.model.jnt_dofadr[jad] for jad in self.actuator_joint_ids]
        )

        self.actuator_joint_dict = {
            n: self.get_joint_id_from_name(n) for n in self.actuator_names
        }

        self._floating_base_qpos_addr = self.model.jnt_qposadr[
            np.where(self.model.jnt_type == 0)
        ][
            0
        ]  # Assuming there is only one floating base! the jnt_type==0 is a floating joint. 3 is a hinge

        self._floating_base_qvel_addr = self.model.jnt_dofadr[
            np.where(self.model.jnt_type == 0)
        ][
            0
        ]  # Assuming there is only one floating base! the jnt_type==0 is a floating joint. 3 is a hinge

        self._floating_base_id = self.model.joint(self.floating_base_name).id

        # self.all_joint_no_backlash_ids=np.zeros(7+self.model.nu)
        all_idx = self.backlash_joint_ids + list(
            range(self._floating_base_qpos_addr, self._floating_base_qpos_addr + 7)
        )
        all_idx.sort()

        # self.all_joint_no_backlash_ids=[idx for idx in self.all_joint_ids if idx not in self.backlash_joint_ids]+list(range(self._floating_base_add,self._floating_base_add+7))
        self.all_joint_no_backlash_ids = [idx for idx in all_idx]

        self.gyro_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SENSOR, "gyro")
        self.gyro_addr = self.model.sensor_adr[self.gyro_id]
        self.gyro_dimensions = 3

        self.accelerometer_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SENSOR, "accelerometer"
        )
        self.accelerometer_dimensions = 3
        self.accelerometer_addr = self.model.sensor_adr[self.accelerometer_id]

        self.linvel_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SENSOR, "local_linvel"
        )
        self.linvel_dimensions = 3

        self.imu_site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, "imu"
        )

        self.gravity_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SENSOR, "upvector"
        )
        self.gravity_dimensions = 3

        self.init_pos = np.array(
            self.get_all_joints_qpos(self.model.keyframe("home").qpos)
        )  # pose of all the joints (no floating base)
        self.default_actuator = self.model.keyframe(
            "home"
        ).ctrl  # ctrl of all the actual joints (no floating base and no backlash)
        self.motor_targets = self.default_actuator
        self.prev_motor_targets = self.default_actuator

        self.data.qpos[:] = self.model.keyframe("home").qpos
        self.data.ctrl[:] = self.default_actuator

    def get_actuator_id_from_name(self, name: str) -> int:
        """Return the id of a specified actuator"""
        return mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)

    def get_joint_id_from_name(self, name: str) -> int:
        """Return the id of a specified joint"""
        return mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name)

    def get_joint_addr_from_name(self, name: str) -> int:
        """Return the address of a specified joint"""
        return self.model.joint(name).qposadr

    def get_dof_id_from_name(self, name: str) -> int:
        """Return the id of a specified dof"""
        return mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_DOF, name)

    def get_actuator_joint_qpos_from_name(
        self, data: np.ndarray, name: str
    ) -> np.ndarray:
        """Return the qpos of a given actual joint"""
        addr = self.model.jnt_qposadr[self.actuator_joint_dict[name]]
        return data[addr]

    def get_actuator_joints_addr(self) -> np.ndarray:
        """Return the all the idx of actual joints"""
        addr = np.array(
            [self.model.jnt_qposadr[idx] for idx in self.actuator_joint_ids]
        )
        return addr

    def get_floating_base_qpos(self, data: np.ndarray) -> np.ndarray:
        return data[self._floating_base_qpos_addr : self._floating_base_qvel_addr + 7]

    def get_floating_base_qvel(self, data: np.ndarray) -> np.ndarray:
        return data[self._floating_base_qvel_addr : self._floating_base_qvel_addr + 6]

    def set_floating_base_qpos(
        self, new_qpos: np.ndarray, qpos: np.ndarray
    ) -> np.ndarray:
        qpos[self._floating_base_qpos_addr : self._floating_base_qpos_addr + 7] = (
            new_qpos
        )
        return qpos

    def set_floating_base_qvel(
        self, new_qvel: np.ndarray, qvel: np.ndarray
    ) -> np.ndarray:
        qvel[self._floating_base_qvel_addr : self._floating_base_qvel_addr + 6] = (
            new_qvel
        )
        return qvel

    def exclude_backlash_joints_addr(self) -> np.ndarray:
        """Return the all the idx of actual joints and floating base"""
        addr = np.array(
            [self.model.jnt_qposadr[idx] for idx in self.all_joint_no_backlash_ids]
        )
        return addr

    def get_all_joints_addr(self) -> np.ndarray:
        """Return the all the idx of all joints"""
        addr = np.array([self.model.jnt_qposadr[idx] for idx in self.all_joint_ids])
        return addr

    def get_actuator_joints_qpos(self, data: np.ndarray) -> np.ndarray:
        """Return the all the qpos of actual joints"""
        return data[self.get_actuator_joints_addr()]

    def set_actuator_joints_qpos(
        self, new_qpos: np.ndarray, qpos: np.ndarray
    ) -> np.ndarray:
        """Set the qpos only for the actual joints (omit the backlash joint)"""
        qpos[self.get_actuator_joints_addr()] = new_qpos
        return qpos

    def get_actuator_joints_qvel(self, data: np.ndarray) -> np.ndarray:
        """Return the all the qvel of actual joints"""
        return data[self.actuator_qvel_addr]

    def set_actuator_joints_qvel(
        self, new_qvel: np.ndarray, qvel: np.ndarray
    ) -> np.ndarray:
        """Set the qvel only for the actual joints (omit the backlash joint)"""
        qvel[self.actuator_qvel_addr] = new_qvel
        return qvel

    def get_all_joints_qpos(self, data: np.ndarray) -> np.ndarray:
        """Return the all the qpos of all joints"""
        return data[self.get_all_joints_addr()]

    def get_all_joints_qvel(self, data: np.ndarray) -> np.ndarray:
        """Return the all the qvel of all joints"""
        return data[self.all_qvel_addr]

    def get_joints_nobacklash_qpos(self, data: np.ndarray) -> np.ndarray:
        """Return the all the qpos of actual joints with the floating base"""
        return data[self.exclude_backlash_joints_addr()]

    def set_complete_qpos_from_joints(
        self, no_backlash_qpos: np.ndarray, full_qpos: np.ndarray
    ) -> np.ndarray:
        """In the case of backlash joints, we want to ignore them (remove them) but we still need to set the complete state incuding them"""
        full_qpos[self.exclude_backlash_joints_addr()] = no_backlash_qpos
        return np.array(full_qpos)

    def get_sensor(self, data, name, dimensions):
        i = self.model.sensor_name2id(name)
        return data.sensordata[i : i + dimensions]

    def get_gyro(self, data):
        return data.sensordata[self.gyro_addr : self.gyro_addr + self.gyro_dimensions]

    def get_accelerometer(self, data):
        return data.sensordata[
            self.accelerometer_addr : self.accelerometer_addr
            + self.accelerometer_dimensions
        ]

    def get_linvel(self, data):
        return data.sensordata[self.linvel_id : self.linvel_id + self.linvel_dimensions]

    # def get_gravity(self, data):
    #     return data.site_xmat[self.imu_site_id].reshape((3, 3)).T @ np.array([0, 0, -1])

    def get_gravity(self, data):
        return data.sensordata[
            self.gravity_id : self.gravity_id + self.gravity_dimensions
        ]

    def check_contact(self, data, body1_name, body2_name):
        body1_id = data.body(body1_name).id
        body2_id = data.body(body2_name).id

        for i in range(data.ncon):
            try:
                contact = data.contact[i]
            except Exception as e:
                return False

            if (
                self.model.geom_bodyid[contact.geom1] == body1_id
                and self.model.geom_bodyid[contact.geom2] == body2_id
            ) or (
                self.model.geom_bodyid[contact.geom1] == body2_id
                and self.model.geom_bodyid[contact.geom2] == body1_id
            ):
                return True

        return False

    def get_feet_contacts(self, data):
        left_contact = self.check_contact(data, "foot_assembly", "floor")
        right_contact = self.check_contact(data, "foot_assembly_2", "floor")
        return left_contact, right_contact


# GLFW key codes (what the MuJoCo viewer passes to key_callback)
KEY_SPACE = 32
KEY_SEMICOLON = 59
KEY_A, KEY_D, KEY_E, KEY_H, KEY_P, KEY_Q, KEY_S, KEY_W = 65, 68, 69, 72, 80, 81, 83, 87
KEY_RIGHT, KEY_LEFT, KEY_DOWN, KEY_UP = 262, 263, 264, 265

CONTROLS = """
+-----------+------------------------------+-------------------+
| Key       | Walk mode                    | Head mode         |
+-----------+------------------------------+-------------------+
| W / Up    | walk forward                 | look up           |
| S / Down  | walk backward                | look down         |
| A / D     | turn left / right            | head yaw L / R    |
| Left/Right| step sideways left / right   | head yaw L / R    |
| Q / E     | turn left / right            | head roll L / R   |
| Space     | stop                         | center head       |
| H         | toggle walk <-> head mode                        |
| P / ;     | step frequency + / -                             |
+-----------+--------------------------------------------------+
A key press sets a command that stays until the next key.
Close the viewer window or press Ctrl+C here to quit.
"""


class MjInfer(MJInferBase):
    def __init__(
        self,
        model_path: str,
        reference_data: str,
        onnx_model_path: str,
        standing: bool,
        save_obs: bool = False,
    ):
        super().__init__(model_path)

        if self.actuator_names != EXPECTED_ACTUATORS:
            raise RuntimeError(
                f"Actuator order {self.actuator_names} does not match the policy's "
                f"expected order {EXPECTED_ACTUATORS}"
            )

        self.standing = standing
        self.head_control_mode = self.standing

        # Params
        self.linearVelocityScale = 1.0
        self.angularVelocityScale = 1.0
        self.dof_pos_scale = 1.0
        self.dof_vel_scale = 0.05
        self.action_scale = 0.25

        if not self.standing:
            self.PRM = PolyReferenceMotion(reference_data)

        self.policy = OnnxInfer(onnx_model_path, awd=True)

        # Command ranges the policy was trained on (upstream values).
        self.COMMANDS_RANGE_X = [-0.15, 0.15]
        self.COMMANDS_RANGE_Y = [-0.2, 0.2]
        self.COMMANDS_RANGE_THETA = [-1.0, 1.0]  # [-1.0, 1.0]

        self.NECK_PITCH_RANGE = [-0.34, 1.1]
        self.HEAD_PITCH_RANGE = [-0.78, 0.78]
        self.HEAD_YAW_RANGE = [-1.5, 1.5]
        self.HEAD_ROLL_RANGE = [-0.5, 0.5]

        self.last_action = np.zeros(self.num_dofs)
        self.last_last_action = np.zeros(self.num_dofs)
        self.last_last_last_action = np.zeros(self.num_dofs)
        # [lin_vel_x, lin_vel_y, ang_vel, neck_pitch, head_pitch, head_yaw, head_roll]
        self.commands = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.imitation_i = 0
        self.imitation_phase = np.array([0, 0])
        self.save_obs = save_obs
        self.saved_obs = []

        self.max_motor_velocity = 5.24  # rad/s

        self.phase_frequency_factor = 1.0

        self._viewer_defaults = None
        self._last_status = None

    def get_obs(
        self,
        data,
        command,  # , qvel_history, qpos_error_history, gravity_history
    ):
        gyro = self.get_gyro(data)
        accelerometer = self.get_accelerometer(data)
        accelerometer[0] += 1.3

        joint_angles = self.get_actuator_joints_qpos(data.qpos)
        joint_vel = self.get_actuator_joints_qvel(data.qvel)

        contacts = self.get_feet_contacts(data)

        obs = np.concatenate(
            [
                gyro,
                accelerometer,
                command,
                joint_angles - self.default_actuator,
                joint_vel * self.dof_vel_scale,
                self.last_action,
                self.last_last_action,
                self.last_last_last_action,
                self.motor_targets,
                contacts,
                self.imitation_phase,
            ]
        )

        return obs

    # ------------------------------------------------------------------ keyboard

    def key_callback(self, keycode):
        if keycode == KEY_H:
            self.head_control_mode = not self.head_control_mode
            self.commands[0:3] = [0.0, 0.0, 0.0]  # stop walking when switching modes
        elif keycode == KEY_P:
            self.phase_frequency_factor += 0.1
        elif keycode == KEY_SEMICOLON:
            self.phase_frequency_factor = max(0.1, self.phase_frequency_factor - 0.1)
        elif not self.head_control_mode:
            walk = {
                KEY_W: (self.COMMANDS_RANGE_X[1], 0, 0),
                KEY_UP: (self.COMMANDS_RANGE_X[1], 0, 0),
                KEY_S: (self.COMMANDS_RANGE_X[0], 0, 0),
                KEY_DOWN: (self.COMMANDS_RANGE_X[0], 0, 0),
                KEY_LEFT: (0, self.COMMANDS_RANGE_Y[1], 0),
                KEY_RIGHT: (0, self.COMMANDS_RANGE_Y[0], 0),
                KEY_A: (0, 0, self.COMMANDS_RANGE_THETA[1]),
                KEY_Q: (0, 0, self.COMMANDS_RANGE_THETA[1]),
                KEY_D: (0, 0, self.COMMANDS_RANGE_THETA[0]),
                KEY_E: (0, 0, self.COMMANDS_RANGE_THETA[0]),
                KEY_SPACE: (0, 0, 0),
            }
            if keycode not in walk:
                return
            self.commands[0:3] = [float(v) for v in walk[keycode]]
        else:
            # Same values as upstream: up/down drive the head_pitch command
            # (commands[4]) with the neck pitch range; neck_pitch stays 0.
            head = {
                KEY_W: (0, self.NECK_PITCH_RANGE[1], 0, 0),
                KEY_UP: (0, self.NECK_PITCH_RANGE[1], 0, 0),
                KEY_S: (0, self.NECK_PITCH_RANGE[0], 0, 0),
                KEY_DOWN: (0, self.NECK_PITCH_RANGE[0], 0, 0),
                KEY_A: (0, 0, self.HEAD_YAW_RANGE[1], 0),
                KEY_LEFT: (0, 0, self.HEAD_YAW_RANGE[1], 0),
                KEY_D: (0, 0, self.HEAD_YAW_RANGE[0], 0),
                KEY_RIGHT: (0, 0, self.HEAD_YAW_RANGE[0], 0),
                KEY_Q: (0, 0, 0, self.HEAD_ROLL_RANGE[1]),
                KEY_E: (0, 0, 0, self.HEAD_ROLL_RANGE[0]),
                KEY_SPACE: (0, 0, 0, 0),
            }
            if keycode not in head:
                return
            self.commands[3:7] = [float(v) for v in head[keycode]]
            self.commands[0:3] = [0.0, 0.0, 0.0]  # upstream: head mode keeps the body still
        self.print_status()

    def print_status(self):
        vx, vy, wz, _, pitch, yaw, roll = self.commands
        if vx > 0:
            walk = "forward"
        elif vx < 0:
            walk = "backward"
        elif vy > 0:
            walk = "sideways left"
        elif vy < 0:
            walk = "sideways right"
        elif wz > 0:
            walk = "turn left"
        elif wz < 0:
            walk = "turn right"
        else:
            walk = "stopped"
        mode = "HEAD" if self.head_control_mode else "WALK"
        status = (
            f"[{mode}] {walk:14s} vx={vx:+.2f} vy={vy:+.2f} yaw_rate={wz:+.2f} | "
            f"head pitch={pitch:+.2f} yaw={yaw:+.2f} roll={roll:+.2f} | "
            f"step freq x{self.phase_frequency_factor:.1f}"
        )
        if status != self._last_status:
            print(status, flush=True)
            self._last_status = status

    def guard_viewer_shortcuts(self, viewer):
        """Undo the viewer's own single-key shortcuts.

        Every letter (W = wireframe, S = shadows, D = hide static bodies, H = convex
        hull, ...), the digits 0-5 (geom groups) and ';' toggle rendering options in
        the MuJoCo viewer, even with its side panels hidden. We snapshot those options
        once and put them back, so our keys only drive the duck.
        """
        if getattr(viewer, "user_scn", None) is None:
            return
        with viewer.lock():
            if self._viewer_defaults is None:
                self._viewer_defaults = (
                    viewer.user_scn.flags.copy(),
                    viewer.opt.flags.copy(),
                    viewer.opt.geomgroup.copy(),
                    viewer.opt.sitegroup.copy(),
                )
                return
            rnd, vis, geom, site = self._viewer_defaults
            viewer.user_scn.flags[:] = rnd
            viewer.opt.flags[:] = vis
            viewer.opt.geomgroup[:] = geom
            viewer.opt.sitegroup[:] = site

    # ---------------------------------------------------------------- main loop

    def run(self):
        print(CONTROLS)
        self.print_status()
        try:
            with mujoco.viewer.launch_passive(
                self.model,
                self.data,
                show_left_ui=False,
                show_right_ui=False,
                key_callback=self.key_callback,
            ) as viewer:
                counter = 0
                while viewer.is_running():

                    step_start = time.time()

                    mujoco.mj_step(self.model, self.data)

                    counter += 1

                    if counter % self.decimation == 0:
                        if not self.standing:
                            self.imitation_i += 1.0 * self.phase_frequency_factor
                            self.imitation_i = (
                                self.imitation_i % self.PRM.nb_steps_in_period
                            )
                            self.imitation_phase = np.array(
                                [
                                    np.cos(
                                        self.imitation_i
                                        / self.PRM.nb_steps_in_period
                                        * 2
                                        * np.pi
                                    ),
                                    np.sin(
                                        self.imitation_i
                                        / self.PRM.nb_steps_in_period
                                        * 2
                                        * np.pi
                                    ),
                                ]
                            )
                        obs = self.get_obs(
                            self.data,
                            self.commands,
                        )
                        if self.save_obs:
                            self.saved_obs.append(obs)
                        action = self.policy.infer(obs)

                        self.last_last_last_action = self.last_last_action.copy()
                        self.last_last_action = self.last_action.copy()
                        self.last_action = action.copy()

                        self.motor_targets = (
                            self.default_actuator + action * self.action_scale
                        )

                        if USE_MOTOR_SPEED_LIMITS:
                            self.motor_targets = np.clip(
                                self.motor_targets,
                                self.prev_motor_targets
                                - self.max_motor_velocity
                                * (self.sim_dt * self.decimation),
                                self.prev_motor_targets
                                + self.max_motor_velocity
                                * (self.sim_dt * self.decimation),
                            )

                            self.prev_motor_targets = self.motor_targets.copy()

                        self.data.ctrl = self.motor_targets.copy()

                        self.guard_viewer_shortcuts(viewer)

                    viewer.sync()

                    time_until_next_step = self.model.opt.timestep - (
                        time.time() - step_start
                    )
                    if time_until_next_step > 0:
                        time.sleep(time_until_next_step)
        except KeyboardInterrupt:
            pass
        finally:
            if self.save_obs:
                with open("mujoco_saved_obs.pkl", "wb") as f:
                    pickle.dump(self.saved_obs, f)
                print(f"Saved {len(self.saved_obs)} observations to mujoco_saved_obs.pkl")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--policy",
        type=str,
        default=str(HERE / "policies" / "BEST_WALK_ONNX_2.onnx"),
        help="ONNX walking policy",
    )
    parser.add_argument(
        "--scene",
        type=str,
        default=str(HERE / "model" / "scene_flat_terrain.xml"),
        help="MuJoCo scene XML",
    )
    parser.add_argument(
        "--reference_data",
        type=str,
        default=str(HERE / "data" / "polynomial_coefficients.pkl"),
        help="reference-motion polynomial coefficients (sets the gait period)",
    )
    parser.add_argument(
        "--standing", action="store_true", default=False, help="standing policy (no gait phase)"
    )
    parser.add_argument(
        "--save_obs",
        action="store_true",
        default=False,
        help="record observations to ./mujoco_saved_obs.pkl on exit",
    )
    args = parser.parse_args()

    mjinfer = MjInfer(
        args.scene, args.reference_data, args.policy, args.standing, args.save_obs
    )
    mjinfer.run()


if __name__ == "__main__":
    main()
