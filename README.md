# brown-duck

Our club's build of the [Open Duck Mini v2](https://github.com/apirrone/Open_Duck_Mini): a ~42 cm
bipedal duck robot with 14 Feetech STS3215 servos, a Raspberry Pi Zero 2W and a BNO055 IMU.
Goal: a stock v2 **walking by early December**, then our own design.

## Join the robotics club e-board

Interested in an e-board position? Fill out the
[e-board application form](https://docs.google.com/forms/d/e/1FAIpQLSfT_RuMOdUsZTs073NgPWlHB3cXlm2mz7AZDz0dPcLtar_VOw/viewform)
or scan the QR code:

<img src="docs/images/eboard-form-qr.png" alt="QR code for the robotics club e-board form" width="200">

## Next lab: Open Duck Mini leg mechanism

Build **one left leg** from the printed foot, shin, thigh and hip parts. Set each servo's
robot ID separately, power the daisy chain through the Waveshare bus servo adapter,
and test a small supported stepping motion. Then explore how a two-link inverse
kinematics calculation turns a desired foot position into hip and knee angles.

Start with the [leg mechanism lab worksheet](activities/leg-mechanism.md). It has the
print checklist, wiring and power steps, assembly order, commands, and a simple gait
exercise. Bring the printed parts, matching-voltage servos, adapter, external servo
supply, USB cable, screws, horns and bearings. One leg can step while held or mounted;
walking across the floor needs the second leg and body.

[![Watch the lower-body assembly video](docs/images/leg-assembly-poster.png)](docs/videos/leg-assembly.mp4)

[Watch the MuJoCo lower-body assembly animation](docs/videos/leg-assembly.mp4) · both legs,
hip mechanisms and the inner pelvis mount, without the exterior covers. The parts and
servo meshes come from the
[Open Duck Mini v2 model](Open_Duck_Mini/mini_bdx/robots/open_duck_mini_v2/robot.xml).
Use the [assembly guide](Open_Duck_Mini/docs/assembly_guide.md) for the exact hardware steps.

### Open the lower-body URDF walking simulator

The [lower-body URDF](sim/model/lower_body.urdf) contains both legs, all ten leg joints,
and the inner pelvis without the outer shell. It uses the original Open Duck Mini v2
joint frames and meshes. Clone the submodule and install the simulator once:

```bash
git submodule update --init --recursive
conda env create -f sim/environment.yml
conda activate brown-duck
```

From the repository root, open the URDF in the MuJoCo viewer:

```bash
mjpython sim/urdf_walk.py         # macOS
python sim/urdf_walk.py           # Linux / Windows
python sim/urdf_walk.py --check   # headless gait check on any OS
```

Close the viewer window to stop. The [URDF walker](sim/urdf_walk.py) alternates a
two-link inverse-kinematics stance and swing for each foot while the pelvis advances.
The [earlier MJCF IK preview](docs/videos/ik-walk.mp4) remains available too.

[![Watch the lower-body URDF walk](docs/images/urdf-walk-poster.png)](docs/videos/urdf-walk.mp4)

This is a supported kinematic demonstration: the pelvis follows a prescribed path.
The extracted URDF uses placeholder inertias and omits collisions, so it is for
kinematic viewing rather than dynamic balance tests. It does not send commands to
real servos. Run
`python sim/urdf_walk.py --video` to regenerate the clip (requires FFmpeg).

### Daisy-chain the assembled leg and run a first motion

Give each servo its own ID **before** connecting the chain. For the left leg, use
hip yaw **20**, hip roll **21**, hip pitch **22**, knee **23**, and ankle **24**.
Read each servo's rated voltage and use a regulated supply at that voltage on the
Waveshare adapter's servo power input; USB carries data, not motor power. All motors
on one chain must have the same rated voltage.

1. Connect the adapter by USB and find its port: `python sim/duck_tools.py find-port`.
   Replace `PORT` below with the reported port.
2. With servo power off, connect **one servo at a time**. Run
   `python sim/duck_tools.py setup-motors --port PORT --robot left-leg` and follow
   its prompts. It assigns the five IDs and centers each servo; remove the horn
   before centering. Power off before changing each cable.
3. With power off, cable **Waveshare adapter → first servo → next servo → ...**
   using each servo's second bus socket. Chain order does not set the IDs.
4. Power on, support the assembled leg, then check and gently move the knee:

   ```bash
   python sim/servo_lab.py status --port PORT --ids 20 21 22 23 24
   python sim/servo_lab.py sweep --port PORT --id 23 --amplitude 5 --speed 40
   ```

Keep the foot clear of the table and stop if any joint binds. The
[leg mechanism worksheet](activities/leg-mechanism.md) covers a three-joint option,
assembly, calibration, and troubleshooting. The URDF walking command above is a
simulation command; the supported `sweep` is the first physical motion.

The previous [servo lab](activities/servo-lab.md) remains available with the same commands
for ID setup, status, angle sweeps and the two-servo demo. The
[mixed-ratio daisy-chain guide](hardware/SERVO_DAISY_CHAIN.md) is also available.

## Folder map

- **`hardware/`**: what to buy and build
  - `BOM.md` / `BOM.csv`: parts list with prices (edit the CSV, regenerate with `make_bom_md.py`)
  - `PRINT_LIST.md`: checklist of all 36 STLs to print, linked into `Open_Duck_Mini/print/`
  - `ASSEMBLY.md`: one-page build order, rules, servo IDs, wiring pins
  - `SERVO_DAISY_CHAIN.md`: wiring and commands for mixed-ratio STS3215 servos
  - `SERVO_VARIANTS.md`: other STS3215 gear ratios and power requirements
- **`activities/`**: meeting worksheets (`leg-mechanism.md`, archived `servo-lab.md`,
  `hardware.md`, `software.md`, `open-ended.md`);
  your ideas go in `activities/ideas/`, your projects in `activities/projects/`
- **`docs/images/`**: sim pictures (regenerate with `docs/render_screenshots.py`)
- **`sim/`**: walking simulator, lower-body URDF (`model/lower_body.urdf`) and IK
  walker (`urdf_walk.py`), the two-servo lab
  (`teleop.py`, `servo_lab.py`), and the
  `brown-duck-*` commands (`duck_tools.py`, installed by `pip install -e .`)
- **`Open_Duck_Mini/`** (git submodule, our fork of upstream): the hardware hub
  - `README.md`: CAD, bill of materials, build-guide links
  - `docs/print_guide.md`: what to 3D print and how
  - `docs/assembly_guide.md`: mechanical assembly
  - `docs/configure_motors.md`: setting servo IDs
  - `docs/open_duck_mini_v2_wiring_diagram.png`: wiring
  - `docs/sim2real.md`: going from sim to the real robot
  - `BEST_WALK_ONNX.onnx`, `BEST_WALK_ONNX_2.onnx`: trained walking policies

## Roadmap

| When | What |
|---|---|
| Previous lab | servo IDs, status, angles, daisy chain, sim + hardware |
| Next lab | configure leg IDs, assemble one leg, bench-step it and try simple IK |
| Then | second leg, head, wiring |
| After that | walking on hardware |
| Early December | demo |

## Links

- Upstream: [Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini) (hardware),
  [Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground) (RL training + sim),
  [Open_Duck_Mini_Runtime](https://github.com/apirrone/Open_Duck_Mini_Runtime) (code on the robot)
- [Open Duck Discord](https://discord.gg/UtJZsgfQGe)
- [tnkr.ai build guide](https://tnkr.ai/explore/docs/open-duck-mini/open-duck-mini-v2#home)
