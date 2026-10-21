"""LeRobot-style commands for the brown-duck servos.

After `pip install -e .` from the repo root these are on your PATH:

    brown-duck-find-port      find the adapter's serial port (unplug/replug)
    brown-duck-setup-motors   give each servo its ID, one servo at a time
    brown-duck-calibrate      record each joint's middle and range to a JSON file
    brown-duck-teleoperate    arrow-key MuJoCo viewer mirrored to two servos
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
from servo_lab import CENTER, Bus

DUCK_IDS = {
    "left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
    "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14,
    "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33,
}
ROBOTS = {
    "lab": {"servo_1": 1, "servo_2": 2},
    "left-leg": {k: v for k, v in DUCK_IDS.items() if k.startswith("left_")},
    "right-leg": {k: v for k, v in DUCK_IDS.items() if k.startswith("right_")},
    "head": {k: v for k, v in DUCK_IDS.items() if k.startswith(("neck", "head"))},
    "duck": DUCK_IDS,
}
TORQUE_ENABLE = 40


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
        input("\nMove every joint by hand to the MIDDLE of its range, then press Enter...")
        middle = {j: bus.position(i) for j, i in joints.items()}
        lows, highs = dict(middle), dict(middle)

        print("\nNow move every joint through its FULL range. Press Enter when done.")
        done = threading.Event()
        threading.Thread(target=lambda: (input(), done.set()), daemon=True).start()
        while not done.is_set():
            for j, i in joints.items():
                p = bus.position(i)
                lows[j], highs[j] = min(lows[j], p), max(highs[j], p)
            line = "  ".join(f"{j}: {lows[j]}–{highs[j]}" for j in joints)
            sys.stdout.write("\r" + line[:200])
            sys.stdout.flush()
            time.sleep(0.05)
    finally:
        bus.close()
    result = {j: {"id": i, "middle": middle[j], "min": lows[j], "max": highs[j]} for j, i in joints.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"\n\nSaved {path}")
    for j, c in result.items():
        print(f"  {j:16} ID {c['id']:3}  middle {c['middle']:4}  range {c['min']}–{c['max']}")


def teleoperate():
    """Like lerobot-teleoperate: arrow keys drive the sim and, with --port, two real servos."""
    sys.argv = [sys.argv[0], "demo", *sys.argv[1:]]
    servo_lab.main()


def servo():
    servo_lab.main()


COMMANDS = {"find-port": find_port, "setup-motors": setup_motors, "calibrate": calibrate,
            "teleoperate": teleoperate, "servo": servo}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    command = COMMANDS[sys.argv.pop(1)]
    sys.exit(command())
