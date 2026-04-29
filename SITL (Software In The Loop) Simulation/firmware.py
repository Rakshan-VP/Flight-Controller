import socket
import json
import time

# =========================
# UDP CONFIG
# =========================
UDP_IP = "127.0.0.1"

# Receive telemetry from Webots
sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_rx.bind((UDP_IP, 9002))
sock_rx.setblocking(False)

# Send motor commands to Webots
sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# =========================
# TEST COMMAND GENERATOR
# =========================
HOVER = 51.0

def generate_test_command(t):
    """
    Simple test pattern:
    - hover baseline
    - small yaw oscillation
    """
    delta = 2.0 * (1 if int(t) % 2 == 0 else -1)

    m1 = HOVER
    m2 = HOVER + delta
    m3 = HOVER
    m4 = HOVER + delta

    return [m1, m2, m3, m4]

# =========================
# MAIN LOOP
# =========================
last_print = 0

while True:
    now = time.time()

    # ---- RECEIVE TELEMETRY ----
    try:
        data, _ = sock_rx.recvfrom(2048)
        telemetry = json.loads(data.decode())

        # Print at ~10 Hz to avoid spam
        if now - last_print > 0.1:
            print("Telemetry:", telemetry)
            last_print = now

    except BlockingIOError:
        pass
    except Exception as e:
        print("RX error:", e)

    # ---- SEND MOTOR COMMAND ----
    try:
        cmd = generate_test_command(now)
        msg = json.dumps(cmd)
        sock_tx.sendto(msg.encode(), (UDP_IP, 9003))

    except Exception as e:
        print("TX error:", e)

    # Small sleep to stabilize loop (~200 Hz max)
    time.sleep(0.005)