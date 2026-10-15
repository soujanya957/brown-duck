# Feetech servo daisy-chain lab

Use this with the [two-servo lab script](../sim/servo_lab.py). Run every command from the
`brown-duck/` repo root in the **same `brown-duck` conda environment** used for the sim:

```bash
conda env create -f sim/environment.yml  # first time only
conda activate brown-duck
# If the environment already exists: conda env update -f sim/environment.yml --prune
python -m serial.tools.list_ports
```

Replace `PORT` in the commands below with your adapter's serial port, such as
`/dev/cu.usbmodem...` on macOS, `/dev/ttyUSB0` or `/dev/ttyACM0` on Linux, or `COM3` on Windows.
The script uses a 1,000,000 baud Feetech STS bus.

## Pick servos that can share power

| STS3215 label | Gear ratio | Rated supply |
|---|---:|---:|
| C046 | 1:147 | 7.4 V |
| C044 | 1:191 | 7.4 V |
| C001 | 1:345 | 7.4 V |
| C018 or C047 (high torque) | 1:345 | 12 V |

Read the **actual label** on each servo and use a supply appropriate for that variant. A daisy
chain shares power: **never put a 7.4 V and a 12 V servo on the same powered chain**. Use a
separate adapter and suitable supply for a 12 V motor. USB connects the board to the computer;
the servos also need external power. Turn power **off** before changing cables. Keep horns and
loose wires clear of moving shafts.

The 147, 191 and 345 ratios change mechanical speed and torque. All of these STS3215 variants
report output position on the same 0–4095 tick scale (one turn), so **do not multiply an angle
by the gear ratio**. `--gear-ratio` and `--gear-ratios` label your motors in the script's output;
`--speed` and `--speeds` change the motion command.

## Assign IDs, one motor at a time

New servos usually have ID 1. Only connect **one servo** while changing its ID. Leave the first
as ID 1 if it already responds. Power off, connect the second servo alone, and set it to ID 2:

```bash
python sim/servo_lab.py status --port PORT --ids 1
python sim/servo_lab.py set-id --port PORT --old-id 1 --new-id 2
```

Power cycle the second servo and verify:

```bash
python sim/servo_lab.py status --port PORT --ids 2
```

For a third compatible servo, repeat the single-servo step using `--new-id 3`. Label each motor
with its **ID, gear ratio, and rated voltage**. If a servo was configured before, use its known
current ID instead of `--old-id 1`. Two servos with the same ID cannot be read reliably on one
bus.

## Connect the chain

With power off, connect **adapter → servo 1 → servo 2** using the spare bus connector on each
servo. A third compatible servo can go after servo 2. Power on, then read each motor:

```bash
# Example: IDs 1, 2, 3 are 1:147, 1:191, 1:345, all rated for the same supply.
python sim/servo_lab.py status --port PORT --ids 1 2 3 --gear-ratios 147 191 345
```

If one ID fails, power off and check its cable and label. Disconnect the others and test it
alone. A servo warning about input voltage is a reason to **stop motion** and check the power
supply and model label.

## Move one motor, then sweep one motor

Remove horns or loads before an absolute angle command: `angle` uses the servo's factory center
of 2048 ticks, which may be far from its current position. Start with a small command and slow
speed:

```bash
python sim/servo_lab.py angle --port PORT --id 1 --degrees 10 --gear-ratio 147 --speed 40
```

`sweep` is gentler for a first test: it reads the **current** position, moves 10° to each side,
and returns to where it started. It refuses a sweep that would exceed the servo's position range
or when the servo reports an error (including an input-voltage error).

```bash
python sim/servo_lab.py sweep --port PORT --id 1 --gear-ratio 147 --amplitude 10 --speed 40
```

Use the same pattern for a 1:191 or 1:345 servo by changing `--id` and `--gear-ratio`. The
gear ratio flag does not change the angle. Keep each servo unloaded and free to move.

## Mirror two motors in MuJoCo

The viewer controls **two selected IDs** at a time; a third servo on the chain remains idle.
The arrow keys send 5° relative steps from each motor's measured starting position, limited to
±30°. Click the viewer first. Left/right controls the first ID; up/down controls the second.

```bash
# macOS
mjpython sim/servo_lab.py demo --port PORT --ids 1 2 --gear-ratios 147 191 --speeds 40 40

# Linux or Windows: use python instead of mjpython
python sim/servo_lab.py demo --port PORT --ids 1 2 --gear-ratios 147 191 --speeds 40 40
```

Close the window to quit. For a simulation with no hardware, omit `--port`.

## If it does not respond

- Confirm the external supply is on and matches every connected servo's **rated voltage**.
- Confirm the USB port with `python -m serial.tools.list_ports` and use that port, not Bluetooth.
- Try `status` with **one servo** and its known ID; the script expects 1,000,000 baud.
- If IDs collide, power off and test each servo alone. Reassign IDs before reconnecting the chain.
- If you see **input voltage error**, stop commands and measure/check the supply. A gear ratio
  flag cannot fix a voltage mismatch.

Model and rating references: [LeRobot SO-101 gear ratios](https://huggingface.co/docs/lerobot/so101),
[Seeed's STS3215 variant and power guide](https://wiki.seeedstudio.com/lerobot_so100m_new/), and
[Feetech's C018 datasheet](https://www.feetech.cn/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf).
