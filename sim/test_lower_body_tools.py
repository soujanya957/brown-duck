"""Hardware-free checks for calibrated, one-joint-at-a-time commands."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import duck_tools


class TeleopSafetyTests(unittest.TestCase):
    def test_small_move_stays_inside_calibration(self):
        limits = {"middle": 2048, "min": 1900, "max": 2200}
        self.assertEqual(duck_tools.checked_teleop_target(2048, 5, limits), 2105)

    def test_rejects_large_or_out_of_range_moves(self):
        limits = {"middle": 2048, "min": 2000, "max": 2100}
        for current, degrees in ((2048, 6), (2090, 5), (1999, -1)):
            with self.subTest(current=current, degrees=degrees), self.assertRaises(ValueError):
                duck_tools.checked_teleop_target(current, degrees, limits)
        with self.assertRaises(ValueError):
            duck_tools.checked_teleop_target(
                2048, 5, {"middle": 2048, "min": 2000, "max": 2120})

    def test_teleop_initializes_only_selected_motor_at_live_position(self):
        class FakeBus:
            def __init__(self):
                self.moves = []
                self.torque = []
                self.packet = self

            def position(self, motor_id):
                self.assert_id(motor_id)
                return 2048

            def assert_id(self, motor_id):
                if motor_id != 23:
                    raise AssertionError(f"Unexpected motor {motor_id}")

            def move(self, motor_id, target, speed):
                self.assert_id(motor_id)
                self.moves.append((motor_id, target, speed))

            def write1ByteTxRx(self, motor_id, address, value):
                self.assert_id(motor_id)
                self.torque.append((motor_id, address, value))
                return (0, 0)

            def check(self, result, error, action):
                if (result, error) != (0, 0):
                    raise AssertionError(f"Unexpected servo error during {action}")

            def close(self):
                pass

        bus = FakeBus()
        calibration = {joint: {"id": motor_id, "middle": 2048, "min": 1900, "max": 2200}
                       for joint, motor_id in duck_tools.ROBOTS["lower-body"].items()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lower-body.json"
            path.write_text(json.dumps(calibration))
            with patch.object(sys, "argv", ["duck_tools.py", "--port", "TEST", "--file", str(path)]), \
                 patch.object(duck_tools, "Bus", return_value=bus), \
                 patch("builtins.input", side_effect=["left_knee +5", "quit"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                duck_tools.joint_teleop()
        self.assertEqual(bus.moves, [(23, 2048, 40), (23, 2105, 40)])
        self.assertEqual(bus.torque, [(23, duck_tools.TORQUE_ENABLE, 1)])


if __name__ == "__main__":
    unittest.main()
