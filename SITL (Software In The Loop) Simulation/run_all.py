import subprocess
import sys
import os
import time

# =========================
# PATHS
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEBOTS_WORLD = os.path.join(
    BASE_DIR,
    "Webots_Model",
    "worlds",
    "Quadcopter.wbt"
)

FIRMWARE = os.path.join(BASE_DIR, "firmware.py")
GUI = os.path.join(BASE_DIR, "GUI.py")

WEBOTS_EXEC = r"C:\Program Files\Webots\msys64\mingw64\bin\webots.exe"


# =========================
# LAUNCHERS
# =========================
def start_webots():
    print("[SYSTEM] Starting Webots...")
    return subprocess.Popen([WEBOTS_EXEC, WEBOTS_WORLD])


def start_firmware():
    print("[SYSTEM] Starting Firmware...")
    return subprocess.Popen([sys.executable, FIRMWARE])


def start_gui():
    print("[SYSTEM] Starting GUI...")
    return subprocess.Popen([sys.executable, GUI])


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    processes = []

    try:
        # 1. Start Webots
        p_webots = start_webots()
        processes.append(p_webots)

        # Give time for Webots to initialize controller
        time.sleep(2)

        # 2. Start firmware
        p_fw = start_firmware()
        processes.append(p_fw)

        # 3. Start GUI
        p_gui = start_gui()
        processes.append(p_gui)

        print("[SYSTEM] All systems running")

        # Wait until GUI exits
        p_gui.wait()

    finally:
        print("[SYSTEM] Shutting down...")

        for p in processes:
            try:
                p.terminate()
            except:
                pass