# Software group worksheet

**Goal:** everyone drives the simulated duck on their own laptop, then understands what the code does.
About 60 minutes. Instructions: [`sim/README.md`](../sim/README.md).

## 1. Setup (30 min)

- Everyone gets `sim/teleop.py` running on their own laptop by following [`sim/README.md`](../sim/README.md).
- **Pair up across operating systems** (macOS / Windows / Linux) so each OS has at least one person
  who got it working and can help the others.
- If the window won't open, run `python sim/test_headless.py` first: `PASS` means your install is fine.
- **Log every problem + fix** in the *Troubleshooting log* table at the bottom of `sim/README.md`
  and open a pull request (one row per problem: OS, Python version, error, fix).

## 2. Explore (20 min)

Write your answers next to each item.

- Drive the duck: W/S, A/D, arrows, Q/E, Space. Which command is it worst at?
- Press **H** for head mode and move the head. Does the body react when the head moves?
- Quit and run `--standing` (`mjpython sim/teleop.py --standing` on macOS). What changes?
  (Hint: look at what `--standing` turns off in `run()`.)
- Press **P** a few times while walking forward, then **;**. At what step frequency does it start to
  stumble? At what frequency does it fall?
- **Push it:** double-click a body part to select it, then **Ctrl + right-drag** to push it.
  How hard a push does it survive from the front? From the side? Does it recover better while walking or standing?

## 3. Understand the loop (10 min)

Read [`sim/teleop.py`](../sim/teleop.py) (`get_obs`, `run`) and answer:

1. What goes into the observation the policy sees? List the pieces and how many numbers each one is.
   How many numbers in total?
2. How often does the policy run (the control frequency, in Hz)? How often does the physics step?
3. What does `action_scale` do? What would happen if it were 1.0 instead of 0.25?

<details>
<summary>Facilitator answers (don't peek)</summary>

1. 101 numbers: gyro (3), accelerometer (3), command (7: vx, vy, yaw rate, neck pitch, head pitch,
   head yaw, head roll), joint angles minus the default pose (14), joint velocities × 0.05 (14),
   the last three actions (3 × 14 = 42), current motor targets (14), foot contacts (2),
   gait phase as cos/sin (2).
2. Physics: every 0.002 s (500 Hz). Policy: every 10 physics steps (`decimation`), so 50 Hz.
3. The policy outputs an offset per joint; the motor target is `default_pose + action × 0.25` (radians).
   It's part of how the policy was trained, so at 1.0 every motion would be 4× bigger and the duck
   would fall. The targets are also clipped so no joint moves faster than 5.24 rad/s.

</details>
