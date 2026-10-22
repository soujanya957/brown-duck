"""LeRobot-style commands for the brown-duck servos.

After `pip install -e .` from the repo root these are on your PATH:

    brown-duck-find-port      find the adapter's serial port (unplug/replug)
    brown-duck-setup-motors   give each servo its ID, one servo at a time
    brown-duck-calibrate      record each joint's middle and range to a JSON file
    brown-duck-teleoperate    arrow-key MuJoCo viewer mirrored to two servos
    brown-duck-joint-teleop   move one calibrated joint at a time in the terminal
    brown-duck-servo          scan / status / set-id / angle / sweep (servo_lab.py)

Without installing, run `python sim/duck_tools.py find-port` (or setup-motors, calibrate, ...).
"""

import argparse
import json
import sys
import threading
import time
from pathlib import Path

import servo_lab
from servo_lab import CENTER, TICKS_PER_TURN, Bus

DUCK_IDS = {
    "left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
    "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14,
    "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33,
}
ROBOTS = {
    "lab": {"servo_1": 1, "servo_2": 2},
    "left-leg": {k: v for k, v in DUCK_IDS.items() if k.startswith("left_")},
    "right-leg": {k: v for k, v in DUCK_IDS.items() if k.startswith("right_")},
    "lower-body": {k: v for k, v in DUCK_IDS.items() if k.startswith(("left_", "right_"))},
    "head": {k: v for k, v in DUCK_IDS.items() if k.startswith(("neck", "head"))},
    "duck": DUCK_IDS,
}
TORQUE_ENABLE = 40
TELEOP_MARGIN_TICKS = round(2 * TICKS_PER_TURN / 360)


def list_ports():
    from serial.tools import list_ports
    return {p.device for p in list_ports.comports()}


def find_port():
    """Like lerobot-find-port: compare the port list before and after unplugging USB."""
    argparse.ArgumentParser(description=find_port.__doc__).parse_args()
    before = list_ports()
    print("Ports now:", ", ".join(sorted(before)) or "none")
    input("Unplug the servo adapter's USB cable, then press Enter...")
    time.sleep(0.5)
    gone = before - list_ports()
    if len(gone) == 1:
        port = gone.pop()
        print(f"\nThe adapter's port is {port}")
        print("Plug the USB cable back in and use it as --port " + port)
    elif not gone:
        print("\nNo port disappeared. Check that the adapter was plugged in, and try another USB cable.")
    else:
        print("\nMore than one port disappeared:", ", ".join(sorted(gone)))


def robot_arg(parser, default):
    parser.add_argument("--robot", choices=ROBOTS, default=default,
                        help=f"which set of joints and IDs to use (default {default})")


def setup_motors():
    """Like lerobot-setup-motors: connect one servo at a time and give it its joint's ID."""
    parser = argparse.ArgumentParser(description=setup_motors.__doc__)
    parser.add_argument("--port", required=True)
    robot_arg(parser, "lab")
    parser.add_argument("--no-center", action="store_true",
                        help="do not move each servo to its center (2048 ticks) after setting the ID")
    args = parser.parse_args()
    bus = Bus(args.port)
    try:
        for joint, new_id in ROBOTS[args.robot].items():
            input(f"\nConnect ONLY the '{joint}' servo (power on), then press Enter...")
            print("Scanning IDs 1–253 (about 15 s)...")
            found = bus.scan(1, 253)
            if len(found) != 1:
                print(f"Expected exactly one servo, found {found or 'none'}. Fix the wiring and run again.")
                return 1
            if found[0] == new_id:
                print(f"'{joint}' already has ID {new_id}.")
            else:
                bus.set_id(found[0], new_id)
                input("Turn servo power off and on again, then press Enter...")
            if not args.no_center:
                input(f"Remove the horn and keep clear: '{joint}' will move to center. Press Enter...")
                bus.check(*bus.packet.write1ByteTxRx(new_id, TORQUE_ENABLE, 1), "enable torque")
                bus.move(new_id, CENTER, 40)
                print("Centered. Fit the horn now if this servo goes into the duck.")
            print(f"Label this servo '{joint}' / ID {new_id}, then unplug it.")
    finally:
        bus.close()
    print("\nAll servos set up.")


def calibrate():
    """Like lerobot-calibrate: record each joint's middle position and range of motion."""
    parser = argparse.ArgumentParser(description=calibrate.__doc__)
    parser.add_argument("--port", required=True)
    robot_arg(parser, "lab")
    parser.add_argument("--file", type=Path, help="output JSON (default calibration/<robot>.json)")
    args = parser.parse_args()
    joints = ROBOTS[args.robot]
    path = args.file or Path("calibration") / f"{args.robot}.json"
    bus = Bus(args.port)
    try:
        for joint, motor_id in joints.items():
            bus.check(*bus.packet.write1ByteTxRx(motor_id, TORQUE_ENABLE, 0), f"disable torque on {joint}")
        print("Torque is off on:", ", ".join(f"{j} (ID {i})" for j, i in joints.items()))
        input("\nMove every joint by hand to its NEUTRAL pose, then press Enter...")
        middle = {j: bus.position(i) for j, i in joints.items()}
        lows, highs = dict(middle), dict(middle)

        print("\nMove each joint gently through its SAFE range. Press Enter when done.")
        done = threading.Event()

        def finish_on_enter():
            try:
                input()
            except EOFError:
                pass
            finally:
                done.set()

        threading.Thread(target=finish_on_enter, daemon=True).start()
        printed_lines = 0
        last_plain_print = 0.0
        while not done.is_set():
            current = {}
            for j, i in joints.items():
                p = bus.position(i)
                current[j] = p
                lows[j], highs[j] = min(lows[j], p), max(highs[j], p)
            if sys.stdout.isatty():
                lines = ["Joint                 ID   Current    Min    Max"]
                lines += [f"{j:20} {i:3}   {current[j]:7} {lows[j]:6} {highs[j]:6}"
                          for j, i in joints.items()]
                lines.append("Press Enter when finished.")
                if printed_lines:
                    sys.stdout.write(f"\x1b[{printed_lines}A")
                for line in lines:
                    sys.stdout.write("\x1b[2K" + line + "\n")
                sys.stdout.flush()
                printed_lines = len(lines)
            elif time.monotonic() - last_plain_print >= 2:
                print("  ".join(f"{j}: {lows[j]}–{highs[j]}" for j in joints))
                last_plain_print = time.monotonic()
            time.sleep(0.15)
    finally:
        bus.close()
    result = {j: {"id": i, "middle": middle[j], "min": lows[j], "max": highs[j]} for j, i in joints.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"\n\nSaved {path}")
    for j, c in result.items():
        print(f"  {j:16} ID {c['id']:3}  middle {c['middle']:4}  range {c['min']}–{c['max']}")


def checked_teleop_target(current, degrees, calibration):
    """Return a small target inside the recorded joint limits, or refuse it."""
    if not -5 <= degrees <= 5 or degrees == 0:
        raise ValueError("Move must be between -5 and +5 degrees, excluding zero")
    low, high = calibration["min"], calibration["max"]
    if not 0 <= low < high <= 4095 or not low <= calibration["middle"] <= high:
        raise ValueError("Calibration has invalid limits or neutral position")
    if not low <= current <= high:
        raise ValueError(f"Current position {current} is outside calibrated range {low}–{high}")
    target = current + round(degrees * TICKS_PER_TURN / 360)
    safe_low, safe_high = low + TELEOP_MARGIN_TICKS, high - TELEOP_MARGIN_TICKS
    if not safe_low <= target <= safe_high:
        raise ValueError(f"Target {target} exceeds buffered range {safe_low}–{safe_high}")
    return target


def joint_teleop():
    """Move one calibrated lower-body motor at a time with small terminal commands."""
    parser = argparse.ArgumentParser(description=joint_teleop.__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--file", type=Path, default=Path("calibration/lower-body.json"))
    args = parser.parse_args()
    if not args.file.exists():
        parser.error(f"{args.file} is missing; calibrate the lower body first")
    calibration = json.loads(args.file.read_text())
    if not isinstance(calibration, dict):
        parser.error(f"{args.file} must contain joint calibration records")
    expected = ROBOTS["lower-body"]
    for joint, motor_id in expected.items():
        if not isinstance(calibration.get(joint), dict) or calibration[joint].get("id") != motor_id:
            parser.error(f"{args.file} needs {joint} at ID {motor_id}")
        values = calibration[joint]
        if any(type(values.get(key)) is not int for key in ("middle", "min", "max")):
            parser.error(f"{args.file} needs integer middle/min/max ticks for {joint}")
        if not 0 <= values["min"] < values["max"] <= 4095 or not values["min"] <= values["middle"] <= values["max"]:
            parser.error(f"{args.file} has invalid limits for {joint}; recalibrate it")
    print("One joint at a time: JOINT +5 or JOINT -5 (degrees). Type 'read' or 'quit'.")
    print("Example: left_knee +5. Each move must stay within recorded limits.")
    bus = Bus(args.port)
    armed_ids = set()
    try:
        while True:
            try:
                command = input("joint> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if command in {"quit", "exit", "q"}:
                break
            if command == "read":
                for joint, motor_id in expected.items():
                    c = calibration[joint]
                    print(f"{joint:20} ID {motor_id:2}  now {bus.position(motor_id):4}  "
                          f"safe {c['min']}–{c['max']}  neutral {c['middle']}")
                continue
            parts = command.split()
            if len(parts) != 2 or parts[0] not in expected:
                print("Use JOINT +5, JOINT -5, read, or quit.")
                continue
            joint = parts[0]
            try:
                degrees = float(parts[1])
                current = bus.position(expected[joint])
                target = checked_teleop_target(current, degrees, calibration[joint])
            except ValueError as exc:
                print(f"No move: {exc}")
                continue
            motor_id = expected[joint]
            if motor_id not in armed_ids:
                # Calibration leaves torque off. Set the goal to the live position
                # before enabling torque, so an old goal cannot cause a jump.
                bus.move(motor_id, current, 40)
                bus.check(*bus.packet.write1ByteTxRx(motor_id, TORQUE_ENABLE, 1),
                          f"enable torque on {joint}")
                armed_ids.add(motor_id)
            bus.move(motor_id, target, 40)
            print(f"{joint}: {current} → {target} ticks ({degrees:+g}° requested)")
    finally:
        bus.close()


def teleoperate():
    """Like lerobot-teleoperate: arrow keys drive the sim and, with --port, two real servos."""
    sys.argv = [sys.argv[0], "demo", *sys.argv[1:]]
    servo_lab.main()


def servo():
    servo_lab.main()


COMMANDS = {"find-port": find_port, "setup-motors": setup_motors, "calibrate": calibrate,
            "joint-teleop": joint_teleop, "teleoperate": teleoperate, "servo": servo}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    command = COMMANDS[sys.argv.pop(1)]
    sys.exit(command())
