# brown-duck

Our club's build of the [Open Duck Mini v2](https://github.com/apirrone/Open_Duck_Mini): a ~42 cm
bipedal duck robot with 14 Feetech STS3215 servos, a Raspberry Pi Zero 2W and a BNO055 IMU.
Goal: a stock v2 **walking by early December**, then our own design.

## Next lab: one leg, hips, and daisy chaining

Build **one left leg**, give its servos unique IDs, connect them through the Waveshare
adapter, and try a small motion with the leg supported. The simulator shows **both
legs and hips** walking with simple inverse kinematics (IK). Bring the printed parts,
five matching-voltage servos, adapter, regulated servo supply, USB and bus cables,
horns, screws, and bearings. The [lab worksheet](activities/leg-mechanism.md) has the
full parts list and assembly details.

### 1. Set up the software

Run commands from the `brown-duck/` repository folder. Install [Miniconda](sim/INSTALL_CONDA.md)
first if needed. Then run:

```bash
git submodule update --init --recursive
conda env create -f sim/environment.yml  # first time only
conda activate brown-duck
```

If the environment already exists, skip `conda env create`.
For a Python virtual environment instead, see the [simulator setup](sim/README.md#option-b-venv).

### 2. Watch the build and open the walking simulator

The assembly animation shows both legs, hip mechanisms, and the inner pelvis without
the outside shell. Use the [assembly guide](Open_Duck_Mini/docs/assembly_guide.md)
for screw placement and the order of real build steps.

[![Watch the lower-body assembly video](docs/images/leg-assembly-poster.png)](docs/videos/leg-assembly.mp4)

Open the [lower-body URDF](sim/model/lower_body.urdf) walking preview in MuJoCo:

```bash
mjpython sim/urdf_walk.py         # macOS: opens the viewer
python sim/urdf_walk.py           # Linux / Windows: opens the viewer
python sim/urdf_walk.py --check   # any OS: check without a window
```

Run the line for your operating system, then close the viewer window to stop.
The [IK controller](sim/urdf_walk.py) alternates the feet while moving a supported
pelvis forward. Watch the result here:

[![Watch the lower-body URDF walk](docs/images/urdf-walk-poster.png)](docs/videos/urdf-walk.mp4)

This preview sets joint positions directly. Its URDF has placeholder inertias and
no collisions, so it does not test balance or drive physical servos. The
[earlier MJCF walking clip](docs/videos/ik-walk.mp4) is also available.

### 3. Give each servo an ID before assembly

The left leg uses **20 hip yaw, 21 hip roll, 22 hip pitch, 23 knee, 24 ankle**.
Read the rated voltage on each servo label. All servos on one chain must have the
same rated voltage; connect a matching regulated supply to the Waveshare adapter's
servo power input. USB carries data, not motor power.

Connect the adapter by USB, then find its serial port:

```bash
python sim/duck_tools.py find-port
```

Follow the prompt to unplug and reconnect USB. Replace `PORT` in the remaining
commands with the port it prints. With servo power **off**, connect only the first
servo. Run the prompted setup for all five servos:

```bash
python sim/duck_tools.py setup-motors --port PORT --robot left-leg
```

The script assigns one ID at a time and centers each servo. Remove its horn before
centering, and turn servo power off before changing cables. Label each servo with its
joint and ID. Then build the leg in **foot → shin → thigh → hip** order using the
[lab worksheet](activities/leg-mechanism.md) and [assembly guide](Open_Duck_Mini/docs/assembly_guide.md).

### 4. Daisy chain and run a small test

With power **off**, connect **adapter → first servo → next servo → ...** using the
second socket on each servo. Chain order does not set the IDs. Power on, support or
clamp the hip, and keep the foot clear of the table. Check all five IDs before moving:

```bash
python sim/servo_lab.py status --port PORT --ids 20 21 22 23 24
python sim/servo_lab.py sweep --port PORT --id 23 --amplitude 5 --speed 40
```

The second command moves the knee a small amount around its current position and
returns. Stop if the mechanism binds. For a three-joint build, calibration, or
troubleshooting, follow the [lab worksheet](activities/leg-mechanism.md). The
simulator walking command above is separate from this physical leg test.

## After both legs and hips are assembled

Repeat the ID and assembly steps for the right leg: **10 hip yaw, 11 hip roll,
12 hip pitch, 13 knee, 14 ankle**. Use `--robot right-leg` during setup. Once every
motor has a unique ID, power off, connect both legs to the adapter, power on,
and confirm all ten motors respond:

```bash
python sim/servo_lab.py status --port PORT --ids 10 11 12 13 14 20 21 22 23 24
```

### 5. Calibrate safe joint limits with a live terminal view

Support the lower body before releasing servo torque. Run:

```bash
python sim/duck_tools.py calibrate --port PORT --robot lower-body
```

The command turns torque off, asks you to place every joint at its **neutral** pose,
then shows the current position and observed minimum and maximum for all ten joints.
Move each joint by hand only through its safe mechanical range; press Enter when done.
It saves `calibration/lower-body.json`. Inspect the file and repeat calibration if a
joint's range looks wrong or was never moved.

### 6. Control one motor at a time, then let students explore

With the lower body still supported, run:

```bash
python sim/duck_tools.py joint-teleop --port PORT
```

At the `joint>` prompt, try `read`, then `left_knee +5` or `left_knee -5`, and
`quit` when finished. Each command moves only the named motor by up to 5° and
refuses a target within 2° of its observed limits. The first move enables torque at
that motor's current position. Students should try one joint at a time and record
which direction the foot moves, where each joint approaches a stop, and whether left and
right joints are mirrored. The [worksheet](activities/leg-mechanism.md) has a
recording table. The servos keep holding position after `quit`; turn off servo
power before unplugging cables.

### 7. Try one IK foot target

Use the URDF viewer to compare a desired foot location with the printed hip, knee,
and ankle angles. For example, `x=0.01 m` forward and `z=-0.145 m` below the hip:

```bash
mjpython sim/urdf_walk.py --target 0.01 -0.145  # macOS
python sim/urdf_walk.py --target 0.01 -0.145    # Linux / Windows
```

Change `x` a little and predict which joints will move before rerunning. These
model angles are not servo ticks; the recorded neutral positions and joint
directions must be mapped before sending IK targets to physical motors.

### 8. Watch the alternating gait

Run `mjpython sim/urdf_walk.py` on macOS or `python sim/urdf_walk.py` on
Linux/Windows to watch the two feet alternate stance and swing. Run
`python sim/urdf_walk.py --check` to verify the gait without a window. This gait
currently runs in the simulator; it is not a physical balance controller.

The [archived servo lab](activities/servo-lab.md) still has its original setup and
two-servo commands. See the [daisy-chain guide](hardware/SERVO_DAISY_CHAIN.md) for
mixed gear ratios and wiring help.

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
| Then | second leg and hips, ten-joint calibration, student teleop, IK and gait preview |
| After that | head, wiring, and hardware walking work |
| Early December | demo |

## Join the robotics club e-board

Interested in an e-board position? Fill out the
[e-board application form](https://docs.google.com/forms/d/e/1FAIpQLSfT_RuMOdUsZTs073NgPWlHB3cXlm2mz7AZDz0dPcLtar_VOw/viewform)
or scan the QR code:

<img src="docs/images/eboard-form-qr.png" alt="QR code for the robotics club e-board form" width="200">

## Links

- Upstream: [Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini) (hardware),
  [Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground) (RL training + sim),
  [Open_Duck_Mini_Runtime](https://github.com/apirrone/Open_Duck_Mini_Runtime) (code on the robot)
- [Open Duck Discord](https://discord.gg/UtJZsgfQGe)
- [tnkr.ai build guide](https://tnkr.ai/explore/docs/open-duck-mini/open-duck-mini-v2#home)
