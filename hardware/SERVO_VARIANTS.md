# Other STS3215 gear ratios and power

The [archived servo lab](../activities/servo-lab.md) only uses the
**12 V, 1:345 high-torque** STS3215 (the one with the square-wave mark, label C018 or C047).
This page covers the other STS3215 variants and how to power them. For wiring a mixed chain step
by step, see the [servo daisy-chain guide](SERVO_DAISY_CHAIN.md).

## Variants

| STS3215 label | Gear ratio | Rated supply |
|---|---:|---:|
| C046 | 1:147 | 7.4 V |
| C044 | 1:191 | 7.4 V |
| C001 | 1:345 | 7.4 V |
| C018 or C047 (high torque) | 1:345 | 12 V |

The duck itself uses the **7.4 V C001** (see [BOM](BOM.md)), not the 12 V version.

## Power

- Read the voltage on each **actual label** and use a supply rated for that variant.
- A daisy chain shares power: **never put 7.4 V and 12 V servos on the same powered bus**.
  Give 12 V motors their own adapter and 12 V supply.
- USB only connects the adapter to the computer; the servos always need external power.
- Turn power **off** before changing cables.
- If `status` shows an input-voltage error, stop all motion and check the supply and the label.
  A gear ratio flag cannot fix a voltage mismatch.

## Gear ratios in `servo_lab.py`

The 1:147, 1:191 and 1:345 variants all report output position on the same 4096-tick scale (one
turn), so the requested angle does **not** get multiplied by the gear ratio. The ratio only
changes mechanical speed and torque.

`--gear-ratio` / `--gear-ratios` label the motors in the script's output; `--speed` / `--speeds`
set the motion speed (default 60, allowed 1–200). Lower-ratio motors are faster, so start slow:

```bash
python sim/servo_lab.py status --port PORT --ids 1 2 --gear-ratios 147 345
python sim/servo_lab.py angle --port PORT --id 1 --degrees 10 --gear-ratio 147 --speed 40
python sim/servo_lab.py sweep --port PORT --id 1 --gear-ratio 147 --amplitude 10 --speed 40
```

For the two-servo viewer with mixed ratios (same order as `--ids`, both rated for the same
supply). On Linux/Windows, use `python` instead of `mjpython`:

```bash
mjpython sim/servo_lab.py demo --port PORT --ids 1 2 --gear-ratios 147 191 --speeds 40 60
```

Model and rating references: [LeRobot SO-101 gear ratios](https://huggingface.co/docs/lerobot/so101),
[Seeed's STS3215 variant and power guide](https://wiki.seeedstudio.com/lerobot_so100m_new/), and
[Feetech's C018 datasheet](https://www.feetech.cn/Data/feetechrc/upload/file/20240507/6385067068652648096680943.pdf).
