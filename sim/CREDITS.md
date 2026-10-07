# Credits

Everything in `sim/` except `teleop.py`'s key handling, `test_headless.py` and the docs comes from
the Open Duck project by Antoine Pirrone (apirrone) and contributors.

| Our path | Upstream source |
|---|---|
| `model/` (MJCF + meshes) | [apirrone/Open_Duck_Playground](https://github.com/apirrone/Open_Duck_Playground) `playground/open_duck_mini_v2/xmls/` |
| `data/polynomial_coefficients.pkl` | Open_Duck_Playground `playground/open_duck_mini_v2/data/` |
| `onnx_infer.py` | Open_Duck_Playground `playground/common/onnx_infer.py` |
| `poly_reference_motion_numpy.py` | Open_Duck_Playground `playground/common/poly_reference_motion_numpy.py` |
| `teleop.py` (inference loop) | Open_Duck_Playground `playground/open_duck_mini_v2/mujoco_infer_base.py` + `mujoco_infer.py` |
| `policies/BEST_WALK_ONNX_2.onnx` | [apirrone/Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini) (Apache-2.0) |

Vendored at Open_Duck_Playground commit `b9be205`.

## License status

- **Open_Duck_Mini** is licensed under Apache-2.0 (see `../Open_Duck_Mini/LICENSE`).
- **Open_Duck_Playground** has **no LICENSE file** at the vendored commit. Without one, the files
  are under default copyright. Ask upstream (GitHub issue or the Open Duck Discord) before making this
  repo public or redistributing `sim/`.
