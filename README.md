# brown-duck

Our club's build of the [Open Duck Mini v2](https://github.com/apirrone/Open_Duck_Mini): a ~42 cm
bipedal duck robot with 14 Feetech STS3215 servos, a Raspberry Pi Zero 2W and a BNO055 IMU.
Goal: a stock v2 **walking by early December**, then our own design.

## Today's goal: drive the duck in simulation

Install the simulator (macOS, Windows or Linux; conda or venv) and drive the duck with the keyboard.
No GPU needed. **→ [sim/README.md](sim/README.md)**

Quick start with conda, from this folder:

```bash
conda env create -f sim/environment.yml && conda activate brown-duck
mjpython sim/teleop.py      # macOS
python sim/teleop.py        # Linux / Windows
```

W/S walk, A/D turn, Space stop, H switches to head control.

## Getting the code

```bash
git clone --recursive https://github.com/soujanya957/brown-duck.git
```

`--recursive` also pulls `Open_Duck_Mini/`. If you already cloned without it, run
`git submodule update --init`. The sim itself doesn't need the submodule.

## Folder map

- **`sim/`**: our jax-free simulator + keyboard teleop (`teleop.py`, `model/`, `policies/`)
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
| This week | everyone runs the sim; order parts; start 3D printing |
| Next week | servos arrive: set IDs, build the first leg |
| Then | second leg, head, wiring |
| After that | walking on hardware |
| Early December | demo |

## Links

- Upstream: [Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini) (hardware),
  [Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground) (RL training + sim),
  [Open_Duck_Mini_Runtime](https://github.com/apirrone/Open_Duck_Mini_Runtime) (code on the robot)
- [Open Duck Discord](https://discord.gg/UtJZsgfQGe)
- [tnkr.ai build guide](https://tnkr.ai/explore/docs/open-duck-mini/open-duck-mini-v2#home)
