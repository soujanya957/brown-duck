# Daisy-chaining STS3215 servos with different gear ratios

This guide wires two or three STS3215 servos with **different gear ratios** (for example a 1:147,
a 1:191 and a 1:345) onto one bus and drives them with the
[two-servo lab script](../sim/servo_lab.py). For the 12 V high-torque lab only, follow the
[main README](../README.md#todays-meeting-servo-lab) instead. Variant details are in
[SERVO_VARIANTS.md](SERVO_VARIANTS.md).

Run every command from the `brown-duck/` repo root in the `brown-duck` conda environment:

```bash
conda env create -f sim/environment.yml  # first time only
conda activate brown-duck
# If the environment already exists: conda env update -f sim/environment.yml --prune
```

## 1. Check that the servos can share one chain

A daisy chain shares **one power supply**, so every servo on it must have the **same rated
voltage**. The gear ratio can differ; the voltage cannot.

| STS3215 label | Gear ratio | Rated supply | Can chain with |
|---|---:|---:|---|
| C046 | 1:147 | 7.4 V | C044, C001 |
| C044 | 1:191 | 7.4 V | C046, C001 |
| C001 | 1:345 | 7.4 V | C046, C044 |
| C018 or C047 (high torque) | 1:345 | 12 V | other 12 V servos only |

So a mixed-ratio chain means the **7.4 V** servos (C046, C044, C001) on a **7.4 V** supply.
**Never put a 12 V servo on a 7.4 V chain**, or a 7.4 V servo on a 12 V chain. Read the actual
label on every servo before you start.

Gear ratio does not change angles: all of these report position on the same 0–4095 tick scale
(one output turn), so `--degrees 10` means 10° on any of them. The ratio changes speed and
torque: 1:147 is fastest and weakest, 1:345 is slowest and strongest. `--gear-ratio(s)` only
labels motors in the script's output.

## 2. Find the port

With power off, connect the adapter's USB cable to the laptop and the **7.4 V** supply to the
adapter's servo power input (USB alone does not power servos). Then:

```bash
brown-duck-find-port            # after pip install -e .; or: python sim/duck_tools.py find-port
```

Or list ports with `python -m serial.tools.list_ports -v`, unplug the USB cable, list again, and
take the one that disappeared (`/dev/cu.usbmodem...` on macOS, `/dev/ttyUSB0` or `/dev/ttyACM0`
on Linux, `COM3` on Windows). Replace `PORT` below with it.

## 3. Give each servo its own ID, one at a time

New servos usually all have **ID 1**, so they must be set up **before** they are chained. Plan
which ID goes to which servo and write it down, for example:

| ID | Label | Ratio |
|---:|---|---:|
| 1 | C046 | 1:147 |
| 2 | C044 | 1:191 |
| 3 | C001 | 1:345 |

For **each** servo in turn:

1. Power **off**. Plug in **only this servo**.
2. Power on and find its current ID:
   ```bash
   python sim/servo_lab.py scan --port PORT          # add --last 253 if nothing is found
   ```
3. If it is not already the planned ID, set it (here it was 1 and should be 2):
   ```bash
   python sim/servo_lab.py set-id --port PORT --old-id 1 --new-id 2
   ```
4. Power cycle, then confirm it answers on the new ID:
   ```bash
   python sim/servo_lab.py status --port PORT --ids 2 --gear-ratios 191
   ```
5. Stick a label on it with **ID, gear ratio and voltage** (e.g. "2 · 1:191 · 7.4 V"). Power off and
   unplug it.

`brown-duck-setup-motors --port PORT` does steps 1–4 for IDs 1 and 2 with prompts. For a third
servo, do it by hand with `--new-id 3`.

## 4. Connect the chain

Only after **every servo has a different ID**:

1. Power **off**.
2. Cable **adapter → servo 1 → servo 2 → servo 3** using the second bus connector on each servo.
   The order along the chain does not matter; IDs do.
3. Power on and read all of them, giving the ratios in the same order as the IDs:
   ```bash
   python sim/servo_lab.py status --port PORT --ids 1 2 3 --gear-ratios 147 191 345
   ```

Every ID should print a position, a voltage near **7.4 V**, and a temperature. If one is
missing, see the troubleshooting list below.

## 5. Move them one at a time

Remove horns and loads first. `angle` moves to an absolute angle from the factory center
(-30 to 30°); start slow:

```bash
python sim/servo_lab.py angle --port PORT --id 1 --degrees 10 --gear-ratio 147 --speed 40
python sim/servo_lab.py angle --port PORT --id 1 --degrees -10 --gear-ratio 147 --speed 40
python sim/servo_lab.py angle --port PORT --id 1 --degrees 0 --gear-ratio 147 --speed 40
```

`sweep` is gentler: it moves ±10° around the **current** position and returns, and refuses if
the servo reports an error:

```bash
python sim/servo_lab.py sweep --port PORT --id 1 --gear-ratio 147 --amplitude 10 --speed 40
python sim/servo_lab.py sweep --port PORT --id 2 --gear-ratio 191 --amplitude 10 --speed 40
python sim/servo_lab.py sweep --port PORT --id 3 --gear-ratio 345 --amplitude 10 --speed 40
```

Watch the difference: with the same `--speed`, the 1:147 servo gets there quickly, while the 1:345
is slower but much harder to stop by hand (do not try while it is powered).

## 6. Mirror two of them in MuJoCo

The viewer drives **two IDs** at a time; any others on the chain stay idle. Give one ratio and
one speed per ID, in the same order:

```bash
# macOS
mjpython sim/servo_lab.py demo --port PORT --ids 1 3 --gear-ratios 147 345 --speeds 40 40
# Linux or Windows
python sim/servo_lab.py demo --port PORT --ids 1 3 --gear-ratios 147 345 --speeds 40 40
```

Click the viewer. ←/→ move the first ID, ↑/↓ the second, 5° per press, up to ±30° from where each
servo started. Close the window to quit.

## If it does not respond

- **One ID missing from `status`:** power off, unplug the others, and `scan` that servo alone. It
  may still have its old ID, or share an ID with another servo.
- **Two servos with the same ID:** both act strangely or neither answers. Power off, test each
  alone, and reassign before reconnecting.
- **Input voltage error:** stop all commands. The supply does not match the servos' rated
  voltage, or a 12 V servo is on a 7.4 V chain. A gear ratio flag cannot fix this.
- **Nothing answers at all:** check the supply is on, the port is the adapter (not Bluetooth),
  and the cable between adapter and the first servo.

Model and rating references: [LeRobot SO-101 gear ratios](https://huggingface.co/docs/lerobot/so101),
[Seeed's STS3215 variant and power guide](https://wiki.seeedstudio.com/lerobot_so100m_new/), and
[Feetech's C018 datasheet](https://www.feetech.cn/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf).
