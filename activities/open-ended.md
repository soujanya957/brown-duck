# Build something you want

The last block of the meeting is yours. **Pick anything** (from the menu below or your own idea),
work alone or in pairs, and **demo it in 2 minutes** at the end of the meeting or next week.
Unfinished is fine; show what you tried.

Put what you make in `activities/projects/<name>/` with a 3-line `README.md`
(see [`projects/README.md`](projects/README.md)) and open a pull request.

## Software

- **easy**: Record and replay a teleop session (log key presses with timestamps, play them back).
- **easy**: A "dance mode": keyframe animation of the head (neck/head pitch, yaw, roll) set to music.
- **medium**: A gamepad or phone controller for the sim, instead of the keyboard.
- **medium**: Plot joint torques (`data.actuator_force`) while walking. Which joint works hardest?
- **hard**: Get the rough-terrain scene working (`--scene sim/model/scene_rough_terrain_backlash.xml`). It loads,
  but the duck starts inside the terrain and falls through; fix the spawn height without editing the model, then see if the policy copes.
- **hard**: Make the duck walk to a target you click in the viewer.
- **hard**: A web dashboard showing the joint angles live.

## Hardware

- **easy**: A print-time and cost tracker for all the plates (spreadsheet or script from `hardware/PRINT_LIST.md`).
- **medium**: Design a custom accessory from the [hardware worksheet](hardware.md) prompts.
- **medium**: A cable-management plan for the leg harness (routing, lengths, sheath).
- **hard**: A servo test jig that holds one STS3215 for testing before assembly.

## Either

- **easy**: A club logo, a name for our duck, a color scheme.
- **easy**: A build log or video plan for the semester.
- **medium**: Read how the walking policy was trained ([`Open_Duck_Mini/docs/sim2real.md`](../Open_Duck_Mini/docs/sim2real.md))
  and explain it to the club next week in 5 minutes.
