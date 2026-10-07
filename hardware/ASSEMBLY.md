# Assembly overview

One-page map of the build. The step-by-step photos are in the upstream
[assembly guide](../Open_Duck_Mini/docs/assembly_guide.md) and the
[tnkr.ai build guide](https://tnkr.ai/explore/docs/open-duck-mini/open-duck-mini-v2); keep the
[Onshape CAD](https://cad.onshape.com/documents/64074dfcfa379b37d8a47762/w/3650ab4221e215a4f65eb7fe/e/0505c262d882183a25049d05)
open while you build. Parts: [BOM.md](BOM.md), [PRINT_LIST.md](PRINT_LIST.md).

Links into `Open_Duck_Mini/` work in a local clone (`git clone --recursive`). On github.com, use
[soujanya957/Open_Duck_Mini](https://github.com/soujanya957/Open_Duck_Mini/tree/v2/docs).

## Rules

1. **Blue Loctite (243) on metal-to-metal screws into the servos. Never on plastic screws.**
2. **Build and test one leg before starting the second.**
3. **Balance the two 18650 cells to the same voltage before putting them in the holder.**
4. Set each servo's ID *before* it goes into the robot: they're hard to reach afterwards.
5. Hip pitch servos have a required orientation (zero position): check the photo in the guide.

## Build order

| # | Step | Guide section | Notes |
|---:|---|---|---|
| 0 | **Configure every servo's ID** | [configure_motors.md](../Open_Duck_Mini/docs/configure_motors.md) | One servo at a time; it moves to zero, then fit the horn. IDs below. |
| 1 | Trunk | [Assemble the trunk](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-trunk) | bearings + inserts in `trunk_bottom`, 2× M3x10 |
| 2 | Feet | [Assemble the feet](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-feet) | TPU sole + PLA, 2× M3x6; press-fit foot switches |
| 3 | Shins | [Assemble the shins](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-shins) | route the ankle servo cable through the sheet |
| 4 | Thighs | [Assemble the thighs](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-thighs) | hip pitch servo orientation matters |
| 5 | Hips | [Assemble the hips](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-hips) | left/right `roll_to_pitch` parts are mirrored |
| 6 | Neck | [Assemble the neck](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-neck) | |
| 7 | Head mechanism | [Assemble the head mechanism](../Open_Duck_Mini/docs/assembly_guide.md#assemble-the-head-mechanism) | fit `head_bot_sheet` + `body_middle_top` now to avoid disassembly later |
| 8 | Servo board + IMU | [servo board](../Open_Duck_Mini/docs/assembly_guide.md#mount-the-servo-driver-board), [IMU](../Open_Duck_Mini/docs/assembly_guide.md#mount-the-imu) | IMU orientation can be configured in software later |
| 9 | Wiring + battery | [Electronics](../Open_Duck_Mini/docs/assembly_guide.md#electronics), [Battery pack](../Open_Duck_Mini/docs/assembly_guide.md#battery-pack) | see below |
| 10 | Head + body shell | [Head](../Open_Duck_Mini/docs/assembly_guide.md#head), [Body](../Open_Duck_Mini/docs/assembly_guide.md#body) | then software: [Open_Duck_Mini_Runtime](https://github.com/apirrone/Open_Duck_Mini_Runtime) (not this semester's first weeks) |

### Servo IDs

From [configure_motors.md](../Open_Duck_Mini/docs/configure_motors.md). Label each servo with its ID as you set it.

| Joint | Left | Right |
|---|---:|---:|
| hip yaw | 20 | 10 |
| hip roll | 21 | 11 |
| hip pitch | 22 | 12 |
| knee | 23 | 13 |
| ankle | 24 | 14 |

| Head joint | ID |
|---|---:|
| neck pitch | 30 |
| head pitch | 31 |
| head yaw | 32 |
| head roll | 33 |

## Wiring

![Open Duck Mini v2 wiring diagram](../Open_Duck_Mini/docs/open_duck_mini_v2_wiring_diagram.png)

([wiring diagram](../Open_Duck_Mini/docs/open_duck_mini_v2_wiring_diagram.png))

Pi Zero 2W header pins, copied from the [assembly guide](../Open_Duck_Mini/docs/assembly_guide.md#electronics):

| Signal | Pi Zero header pin | Pi function |
|---|---:|---|
| **BNO055** VIN | 1 | 3V3 |
| BNO055 3VO | NC | - |
| BNO055 GND | 9 | GND |
| BNO055 SDA | 3 | GPIO 2 |
| BNO055 SCL | 5 | GPIO 3 |
| BNO055 RST | NC | - |
| **Foot switch** left | 15 | GPIO 22 |
| Foot switch right | 13 | GPIO 27 |
| Foot switch GND | 9 | GND |

The guide's table also covers the optional eye LEDs, projector, antenna servos and MAX98357A speaker amp.
