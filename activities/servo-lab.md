# Servo lab (archived)

Work in **3–4 groups**. Each group gets **two high-torque Feetech STS3215 servos** (the ones with
the **square-wave mark** on the label), **one Waveshare bus servo adapter, a 12 V servo power
supply, and a USB cable**. Bring a laptop with this repo and the `brown-duck` conda environment.
The goal is to give each servo a unique ID, read its status, command a small angle, then connect
both on one bus. After that, try the two-servo simulation and mirror it to the real servos.

These are the **12 V, 1:345** high-torque STS3215 units (label **C018** or **C047**). Check that
both labels say **12 V** before powering anything. The lab only uses these motors. For other gear
ratios (1:147, 1:191, 7.4 V 1:345) and their power rules, see
[hardware/SERVO_VARIANTS.md](../hardware/SERVO_VARIANTS.md). To chain servos with different gear ratios,
follow [hardware/SERVO_DAISY_CHAIN.md](../hardware/SERVO_DAISY_CHAIN.md).

### 1. Get ready

```bash
git clone --recursive https://github.com/soujanya957/brown-duck.git
cd brown-duck
conda env create -f sim/environment.yml
conda activate brown-duck
```

Already cloned? Run `git pull && git submodule update --init`, then
`conda env update -f sim/environment.yml --prune` and `conda activate brown-duck`.
No conda yet? Follow [sim/INSTALL_CONDA.md](../sim/INSTALL_CONDA.md), or the
[venv instructions](../sim/README.md#option-b-venv). Run all commands below from `brown-duck/`.

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
`right-leg`, `head`, or `duck` for the real joint IDs in [hardware/ASSEMBLY.md](../hardware/ASSEMBLY.md).
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
python sim/servo_lab.py angle --port PORT --id 2 --degrees 10 --speed 40   # +10° one way
python sim/servo_lab.py angle --port PORT --id 2 --degrees -10 --speed 40  # -10° the other way
python sim/servo_lab.py angle --port PORT --id 2 --degrees 0 --speed 40    # back to center
python sim/servo_lab.py status --port PORT --ids 2
```

`--degrees` is an absolute target measured from center (any value from -30 to 30), not a step:
running `--degrees 10` twice does not move it a second time. Use a negative number to go the
other direction.

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

The full walking duck sim is still available: [sim/README.md](../sim/README.md).


For the next build, see the [leg mechanism lab](leg-mechanism.md).
