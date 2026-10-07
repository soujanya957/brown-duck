# Hardware group worksheet

**Goal:** understand how the printed parts make up the robot, then come up with our own parts.
About 60 minutes. You need a clone of this repo with the submodule:
`git clone --recursive https://github.com/soujanya957/brown-duck.git`

## Design rules (read first)

1. **Don't change leg geometry, joint positions or servo mounts this semester.** The walking policy
   was trained on this exact robot; change the legs and it stops walking.
2. **Keep added mass small and close to the center.** The whole duck is about 2.1 kg in the sim
   model. Upstream's body-cover mod notes that shifting mass makes the trained policy wobblier.
   Weigh or estimate every new part (your slicer shows the mass estimate) and write it down.
3. **Mount to existing M3 screw holes / heat-set inserts** wherever possible, instead of glue or new holes
   in structural parts.

## 1. Explore (20 min)

Open STLs from [`Open_Duck_Mini/print/`](../Open_Duck_Mini/print/) in a slicer or viewer:
Bambu Studio, PrusaSlicer, or the free online viewer at [viewstl.com](https://www.viewstl.com).
Keep the [Onshape CAD](https://cad.onshape.com/documents/64074dfcfa379b37d8a47762/w/3650ab4221e215a4f65eb7fe/e/0505c262d882183a25049d05)
of the assembled robot open next to it.

- Split the [print list](../hardware/PRINT_LIST.md) sections between you (feet, legs, hips, trunk, neck + head, body shell, extras).
- For each part, find it on the assembled robot in the CAD.
- Fill in the **subassembly** column of [`hardware/PRINT_LIST.md`](../hardware/PRINT_LIST.md) with where it goes
  (e.g. "left foot, top plate", "hip yaw → roll bracket").
- Questions to answer as a group: which parts carry load between two servos? Which parts are only covers?
  Which part would you least like to reprint (longest print)?

## 2. Plan printing (10 min)

- Decide who prints which plate on which printer, and write your name in the **printed by** column.
- Bambu printers: the [MakerWorld profile](https://makerworld.com/en/models/2755651) has all parts on 6 plates (~53 h total).
- **Feet and leg sheets first**, since we build and test one leg before anything else.
- `foot_bottom_tpu.stl` is **TPU at 40 % infill**; everything else is PLA at 15 %.
- If a printer is free today, start the first plate before you leave.

## 3. Ideate our own parts (30 min)

Sketch or model ideas. **One page per idea** in `activities/ideas/<your-name>-<idea>.md`, with a sketch
photo or CAD screenshot next to it (copy [`ideas/TEMPLATE.md`](ideas/TEMPLATE.md)). Prompts:

- A Brown-themed head, eyes or shell. See [`Open_Duck_Mini/print/mods/`](../Open_Duck_Mini/print/mods/)
  for two community examples (Justin's Park head, Jaime's BD-X covers).
- A display stand, carry handle or charging dock.
- Cable guides and covers for the legs.
- A bumper or "fall cage" to protect the head during testing.
- Swappable accessories that don't touch the leg mechanics: hat, tail, name plate.

For each idea, note: estimated mass, where it mounts (which existing holes), and what it would cost to print.
Open a pull request with your idea pages.
