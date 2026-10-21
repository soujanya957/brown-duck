# brown-duck

Our club's build of the [Open Duck Mini v2](https://github.com/apirrone/Open_Duck_Mini): a ~42 cm
bipedal duck robot with 14 Feetech STS3215 servos, a Raspberry Pi Zero 2W and a BNO055 IMU.
Goal: a stock v2 **walking by early December**, then our own design.

## Today's meeting: servo lab

Work in **3–4 groups**. Each group gets **two high-torque Feetech STS3215 servos** (the ones with
the **square-wave mark** on the label), **one Waveshare bus servo adapter, a 12 V servo power
supply, and a USB cable**. Bring a laptop with this repo and the `brown-duck` conda environment.
The goal is to give each servo a unique ID, read its status, command a small angle, then connect
both on one bus. After that, try the two-servo simulation and mirror it to the real servos.

These are the **12 V, 1:345** high-torque STS3215 units (label **C018** or **C047**). Check that
both labels say **12 V** before powering anything. The lab only uses these motors. For other gear
ratios (1:147, 1:191, 7.4 V 1:345) and their power rules, see
[hardware/SERVO_VARIANTS.md](hardware/SERVO_VARIANTS.md).

### 1. Get ready

```bash
git clone --recursive https://github.com/soujanya957/brown-duck.git
cd brown-duck
conda env create -f sim/environment.yml
conda activate brown-duck
```

Already cloned? Run `git pull && git submodule update --init`, then
`conda env update -f sim/environment.yml --prune` and `conda activate brown-duck`.
No conda yet? Follow [sim/INSTALL_CONDA.md](sim/INSTALL_CONDA.md), or the
[venv instructions](sim/README.md#option-b-venv). Run all commands below from `brown-duck/`.

**Optional: LeRobot-style commands.** Run `pip install -e .` once (in the `brown-duck`
environment) to get these shortcuts, modeled on `lerobot-find-port`, `lerobot-setup-motors`, etc.:

| Command | Does | LeRobot equivalent |
|---|---|---|
| `brown-duck-find-port` | unplug/replug the adapter's USB to find its port | `lerobot-find-port` |
| `brown-duck-setup-motors --port PORT` | prompts for one servo at a time, finds it, sets its ID, centers it | `lerobot-setup-motors` |
| `brown-duck-calibrate --port PORT` | torque off; record each joint's middle and range to `calibration/lab.json` | `lerobot-calibrate` |
| `brown-duck-teleoperate --port PORT --ids 1 2` | arrow-key MuJoCo viewer mirrored to two servos (`mjpython $(which brown-duck-teleoperate) ...` on macOS) | `lerobot-teleoperate` |
| `brown-duck-servo scan/status/set-id/angle/sweep ...` | same as `python sim/servo_lab.py ...` | — |

`setup-motors` and `calibrate` default to `--robot lab` (IDs 1 and 2). Use `--robot left-leg`,
`right-leg`, `head`, or `duck` for the real joint IDs in [hardware/ASSEMBLY.md](hardware/ASSEMBLY.md).
Without installing, use `python sim/duck_tools.py find-port` (or `setup-motors`, `calibrate`, ...).

### 2. Wire and find the port

Power **off** while plugging servos in. Connect the **12 V** supply to the adapter's servo power
input with the correct polarity; USB alone does not power the servos. Plug **one servo** into the
adapter and connect the adapter's USB cable to the laptop. Keep the servo horns clear of fingers
and loose cables.

**Find the port.** Run `brown-duck-find-port` (or `python sim/duck_tools.py find-port`) and follow
the prompt. To do it by hand: with the conda environment active, list serial ports, unplug the adapter's
USB cable, and list them again. The entry that disappeared is your adapter:

```bash
python -m serial.tools.list_ports -v
```

| OS | Typical adapter port | Ignore |
|---|---|---|
| macOS | `/dev/cu.usbmodem...` or `/dev/cu.usbserial-...` | `/dev/cu.Bluetooth...`, `/dev/cu.debug-console`, `/dev/cu.wlan-debug` |
| Linux | `/dev/ttyUSB0` or `/dev/ttyACM0` | `/dev/ttyS*` |
| Windows | `COM3`, `COM4`, ... (also in Device Manager → Ports) | `COM1` |

On macOS use the `/dev/cu.` name, not `/dev/tty.`. On Linux, if you get "permission denied", run
`sudo usermod -aG dialout $USER` and log out and back in. If no new port appears, try another USB
cable (some only charge) and check the adapter's driver.

In every command below, replace `PORT` with that name, for example
`--port /dev/cu.usbmodem5A7A0185861`. It is not a shell variable.

### 3. One servo at a time: ID, status, angle

Every servo on a bus needs its **own ID**. New servos usually come set to ID 1, so two new servos
on one bus would collide. Set the IDs **with only one servo connected**.
`brown-duck-setup-motors --port PORT` walks through the steps below for you; here they are by hand.

**Servo 1.** With just the first servo plugged in and powered, find its current ID:

```bash
python sim/servo_lab.py scan --port PORT
```

This pings IDs 1–20 and prints `Found ID n`. (Add `--last 253` to check every ID if nothing
answers.) If it found ID 1, leave it. If it found another ID, say 5, change it to 1:

```bash
python sim/servo_lab.py set-id --port PORT --old-id 5 --new-id 1
```

**Servo 2.** Turn power off, unplug servo 1, plug in servo 2, and turn power on. Scan again, then
set it to ID 2 (here it started at ID 1):

```bash
python sim/servo_lab.py scan --port PORT
python sim/servo_lab.py set-id --port PORT --old-id 1 --new-id 2
```

`set-id` turns torque off and saves the new ID in the servo's memory, so it keeps it after power
off. **Power cycle** the servo, then confirm it answers on the new ID:

```bash
python sim/servo_lab.py status --port PORT --ids 2
```

`status` prints position, voltage (should be near 12 V) and temperature. Label the servos **1** and
**2**. With just servo 2 connected, try a small position command (degrees relative to the servo's
factory center):

```bash
python sim/servo_lab.py angle --port PORT --id 2 --degrees 10 --speed 40
python sim/servo_lab.py status --port PORT --ids 2
```

Remove any horn or load before commanding a position: a servo can move to its factory center.
For a first motion test, `sweep` moves only ±10° from the **current** position and returns:

```bash
python sim/servo_lab.py sweep --port PORT --id 2 --amplitude 10 --speed 40
```

The demo limits angle commands to ±30°. Do not force a powered servo by hand; these motors are
strong. A servo that reports an input-voltage error must have its power issue corrected before a
sweep. The `status` line should read close to 12 V.

### 4. Daisy chain and compare sim with hardware

Power off, connect both servos on the same bus with their separate IDs, then power on:

```bash
python sim/servo_lab.py status --port PORT --ids 1 2
```

First run the two-servo simulation alone. On macOS use `mjpython`; on Linux and Windows use
`python` (Windows path: `sim\servo_lab.py`):

```bash
mjpython sim/servo_lab.py demo                                    # macOS, sim only
mjpython sim/servo_lab.py demo --port PORT --ids 1 2 --speeds 40 40  # macOS, sim + hardware
```

On Linux/Windows, replace `mjpython` with `python`. Click the viewer, then use **←/→** for servo
1 and **↑/↓** for servo 2. Each press changes its target by 5°, up to ±30°. In hardware mode,
those same relative commands go to the two physical servos, starting from their measured
positions when the viewer opens. Keep both motors free to turn.

**Try to explain:** Why must IDs differ on one bus? Which values in `status` are measurements,
and which command sets a target? What happens to the sim when a hardware command fails?

The full walking duck sim is still available: [sim/README.md](sim/README.md).

### 5. Minimal prints for one leg

For a first **left leg mechanism** (hip, shin and foot), print these parts from
[`Open_Duck_Mini/print/`](Open_Duck_Mini/print/). This is **14 printed pieces**, plus the servos,
horns, screws and bearings needed for assembly. The [full print list](hardware/PRINT_LIST.md)
covers the complete duck.

| Piece | Qty |
|---|---:|
| [`roll_motor_top.stl`](Open_Duck_Mini/print/roll_motor_top.stl), [`roll_motor_bottom.stl`](Open_Duck_Mini/print/roll_motor_bottom.stl) | 1 each |
| [`left_roll_to_pitch.stl`](Open_Duck_Mini/print/left_roll_to_pitch.stl), [`left_cache.stl`](Open_Duck_Mini/print/left_cache.stl) | 1 each |
| [`knee_to_ankle_left_sheet.stl`](Open_Duck_Mini/print/knee_to_ankle_left_sheet.stl), [`knee_to_ankle_right_sheet.stl`](Open_Duck_Mini/print/knee_to_ankle_right_sheet.stl), [`leg_spacer.stl`](Open_Duck_Mini/print/leg_spacer.stl) | 2 each |
| [`foot_top.stl`](Open_Duck_Mini/print/foot_top.stl), [`foot_side.stl`](Open_Duck_Mini/print/foot_side.stl), [`foot_bottom_pla.stl`](Open_Duck_Mini/print/foot_bottom_pla.stl), [`foot_bottom_tpu.stl`](Open_Duck_Mini/print/foot_bottom_tpu.stl) | 1 each |

PLA at 15% infill for the rigid pieces; TPU at 40% for `foot_bottom_tpu.stl`. The
[assembly guide](Open_Duck_Mini/docs/assembly_guide.md) shows the foot, shin, thigh and hip order.

### 6. View only the sim legs

This command opens the **two legs from the duck model** with the trunk and head hidden. The hips
are fixed in place while the knees bend slowly, so it is a mechanism viewer rather than a walking
simulation. Run from the same `brown-duck` conda environment:

```bash
mjpython sim/legs.py  # macOS
python sim/legs.py    # Linux / Windows
```

![Two articulated Open Duck Mini legs in MuJoCo](docs/images/legs-only.png)

To save a new still: `python sim/legs.py --preview docs/images/legs-only.png`.

## Folder map

- **`hardware/`**: what to buy and build
  - `BOM.md` / `BOM.csv`: parts list with prices (edit the CSV, regenerate with `make_bom_md.py`)
  - `PRINT_LIST.md`: checklist of all 36 STLs to print, linked into `Open_Duck_Mini/print/`
  - `ASSEMBLY.md`: one-page build order, rules, servo IDs, wiring pins
  - `SERVO_DAISY_CHAIN.md`: wiring and commands for mixed-ratio STS3215 servos
  - `SERVO_VARIANTS.md`: other STS3215 gear ratios and power requirements
- **`activities/`**: meeting worksheets (`hardware.md`, `software.md`, `open-ended.md`);
  your ideas go in `activities/ideas/`, your projects in `activities/projects/`
- **`docs/images/`**: sim pictures (regenerate with `docs/render_screenshots.py`)
- **`sim/`**: walking simulator, the two-servo lab (`teleop.py`, `servo_lab.py`), and the
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
| This week | servo lab: IDs, status, angles, daisy chain, sim + hardware |
| Next week | configure the robot IDs and start the first leg |
| Then | second leg, head, wiring |
| After that | walking on hardware |
| Early December | demo |

## Links

- Upstream: [Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini) (hardware),
  [Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground) (RL training + sim),
  [Open_Duck_Mini_Runtime](https://github.com/apirrone/Open_Duck_Mini_Runtime) (code on the robot)
- [Open Duck Discord](https://discord.gg/UtJZsgfQGe)
- [tnkr.ai build guide](https://tnkr.ai/explore/docs/open-duck-mini/open-duck-mini-v2#home)
