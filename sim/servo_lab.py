"""Two STS3215 servos: inspect, assign IDs, move, and mirror a MuJoCo demo.

Run from the repository root. The viewer needs mjpython on macOS.
"""

import argparse
import math
import time

TICKS_PER_TURN = 4096
CENTER = 2048
MAX_DEGREES = 30
BAUD = 1_000_000


def sdk():
    try:
        from scservo_sdk import COMM_SUCCESS, PortHandler, sms_sts
    except ImportError as exc:
        raise SystemExit("Install the lab dependencies: conda env update -f sim/environment.yml --prune") from exc
    return COMM_SUCCESS, PortHandler, sms_sts


class Bus:
    def __init__(self, port):
        self.success, handler, packet = sdk()
        self.port = handler(port)
        if not self.port.openPort():
            raise RuntimeError(f"Could not open {port}")
        if not self.port.setBaudRate(BAUD):
            self.port.closePort()
            raise RuntimeError(f"Could not set {BAUD} baud on {port}")
        self.packet = packet(self.port)

    def close(self):
        self.port.closePort()

    def check(self, result, error, action):
        if result != self.success:
            raise RuntimeError(f"{action}: {self.packet.getTxRxResult(result)}")
        if error:
            raise RuntimeError(f"{action}: {self.packet.getRxPacketError(error)}")

    def position(self, motor_id):
        value, result, error = self.packet.ReadPos(motor_id)
        self.check(result, error, f"read ID {motor_id}")
        return value

    def status(self, motor_id):
        position = self.position(motor_id)
        voltage, result, error = self.packet.read1ByteTxRx(motor_id, 62)
        self.check(result, error, f"voltage ID {motor_id}")
        temperature, result, error = self.packet.read1ByteTxRx(motor_id, 63)
        self.check(result, error, f"temperature ID {motor_id}")
        print(f"ID {motor_id}: position {position} ticks ({(position-CENTER)*360/TICKS_PER_TURN:+.1f}° from center), voltage {voltage/10:.1f} V, temperature {temperature}°C")

    def move(self, motor_id, ticks):
        if not 0 <= ticks <= 4095:
            raise ValueError("Target outside 0–4095 ticks")
        result, error = self.packet.WritePosEx(motor_id, ticks, 200, 20)
        self.check(result, error, f"move ID {motor_id}")

    def set_id(self, old_id, new_id):
        self.position(old_id)
        result, error = self.packet.write1ByteTxRx(old_id, 40, 0)  # torque off
        self.check(result, error, "disable torque")
        result, error = self.packet.unLockEprom(old_id)
        self.check(result, error, "unlock EEPROM")
        result, error = self.packet.write1ByteTxRx(old_id, 5, new_id)
        self.check(result, error, "write ID")
        result, error = self.packet.LockEprom(new_id)
        self.check(result, error, "lock EEPROM")
        self.position(new_id)
        print(f"ID changed: {old_id} → {new_id}. Torque is off; power cycle before moving it.")


def viewer(bus, ids):
    import mujoco
    import mujoco.viewer

    xml = '''<mujoco model="two servo lab">
      <option timestep="0.01" gravity="0 0 0"/>
      <worldbody>
        <geom type="plane" size="1 1 .01" rgba=".15 .18 .22 1"/>
        <body name="servo_1" pos="-.25 0 .12">
          <joint name="axis_1" type="hinge" axis="0 0 1" limited="true" range="-30 30" damping=".1"/>
          <geom type="box" size=".18 .025 .025" pos=".18 0 0" rgba=".2 .7 1 1" mass=".1"/>
        </body>
        <body name="servo_2" pos=".25 0 .12">
          <joint name="axis_2" type="hinge" axis="0 0 1" limited="true" range="-30 30" damping=".1"/>
          <geom type="box" size=".18 .025 .025" pos=".18 0 0" rgba="1 .55 .2 1" mass=".1"/>
        </body>
      </worldbody>
      <actuator>
        <position joint="axis_1" kp="20"/>
        <position joint="axis_2" kp="20"/>
      </actuator>
    </mujoco>'''
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    angles = [0, 0]
    origins = [bus.position(i) for i in ids] if bus else None
    if origins:
        print(f"Hardware starting positions: ID {ids[0]}={origins[0]}, ID {ids[1]}={origins[1]} ticks")
    print("Click viewer. ←/→ move servo 1, ↑/↓ move servo 2; each press is 5°. Close window to quit.")

    def key_callback(key):
        changes = {263: (0, -5), 262: (0, 5), 265: (1, 5), 264: (1, -5)}
        if key not in changes:
            return
        axis, step = changes[key]
        target = max(-MAX_DEGREES, min(MAX_DEGREES, angles[axis] + step))
        if target == angles[axis]:
            return
        if bus:
            ticks = origins[axis] + round(target * TICKS_PER_TURN / 360)
            if not 0 <= ticks <= 4095:
                print(f"ID {ids[axis]}: target exceeds servo range; ignored")
                return
            try:
                bus.move(ids[axis], ticks)
            except RuntimeError as exc:
                print(exc)
                return
        angles[axis] = target
        print(f"Servo {axis+1}: {target:+d}°" + (f" (ID {ids[axis]})" if bus else ""))

    with mujoco.viewer.launch_passive(model, data, key_callback=key_callback) as window:
        while window.is_running():
            start = time.monotonic()
            data.ctrl[:] = [math.radians(a) for a in angles]
            mujoco.mj_step(model, data)
            window.sync()
            time.sleep(max(0, model.opt.timestep - (time.monotonic() - start)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "set-id", "angle", "demo"):
        p = sub.add_parser(name)
        if name != "demo":
            p.add_argument("--port", required=True, help="serial port, e.g. /dev/tty.usbmodem... or COM3")
        else:
            p.add_argument("--port", help="add hardware mirroring; omit for simulation only")
            p.add_argument("--ids", nargs=2, type=int, default=[1, 2], metavar=("FIRST", "SECOND"))
        if name == "status":
            p.add_argument("--ids", nargs="+", type=int, required=True)
        elif name == "set-id":
            p.add_argument("--old-id", type=int, required=True)
            p.add_argument("--new-id", type=int, required=True)
        elif name == "angle":
            p.add_argument("--id", type=int, required=True)
            p.add_argument("--degrees", type=float, required=True, help="within ±30° of factory center (2048 ticks)")
    args = parser.parse_args()
    if args.command == "angle" and not -MAX_DEGREES <= args.degrees <= MAX_DEGREES:
        parser.error("--degrees must be between -30 and 30")
    if args.command == "set-id" and (not 1 <= args.old_id <= 253 or not 1 <= args.new_id <= 253 or args.old_id == args.new_id):
        parser.error("IDs must be different and between 1 and 253")
    if args.command == "demo" and (len(set(args.ids)) != 2 or any(not 1 <= i <= 253 for i in args.ids)):
        parser.error("--ids needs two distinct IDs between 1 and 253")
    bus = Bus(args.port) if args.port else None
    try:
        if args.command == "status":
            for motor_id in args.ids:
                bus.status(motor_id)
        elif args.command == "set-id":
            bus.set_id(args.old_id, args.new_id)
        elif args.command == "angle":
            ticks = CENTER + round(args.degrees * TICKS_PER_TURN / 360)
            bus.move(args.id, ticks)
            print(f"ID {args.id}: commanded {args.degrees:+.1f}° ({ticks} ticks)")
        else:
            viewer(bus, args.ids)
    finally:
        if bus:
            bus.close()


if __name__ == "__main__":
    main()
