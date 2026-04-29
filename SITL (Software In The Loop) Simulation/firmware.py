import socket
import json
import time

# =========================
# UDP CONFIG (ONLY CONTROL LINK)
# =========================
UDP_IP = "127.0.0.1"

# Send motor commands to control.py
sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Receive telemetry from control.py
sock_telemetry = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_telemetry.bind((UDP_IP, 9002))
sock_telemetry.setblocking(False)

# =========================
# STATE
# =========================
target_z = 10.0   # 🔥 SET YOUR ALTITUDE HERE
current_z = 0.0
vz = 0.0

# =========================
# PID
# =========================
class PID:
    def __init__(self, kp, ki, kd, limit=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.limit = limit

        self.integral = 0
        self.prev_error = 0

    def update(self, error, dt):
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        self.prev_error = error

        out = (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )

        if self.limit:
            out = max(-self.limit, min(self.limit, out))

        return out

# =========================
# CONTROLLER PARAMS
# =========================
pid_z = PID(kp=6.0, ki=1.5, kd=0.0, limit=20)
HOVER = 50.0  

# =========================
# HELPERS
# =========================
def send_motor(v):
    cmd = [v, v, v, v]
    sock_tx.sendto(json.dumps(cmd).encode(), (UDP_IP, 9003))

# =========================
# MAIN LOOP
# =========================
last = time.time()

print(f"[SYSTEM] Holding altitude at {target_z} m")

while True:
    now = time.time()
    dt = now - last
    last = now

    # ---- RECEIVE TELEMETRY ----
    try:
        data, _ = sock_telemetry.recvfrom(2048)
        telemetry = json.loads(data.decode())
        current_z = telemetry[2]
        vz = telemetry[5]
    except BlockingIOError:
        pass
    except Exception as e:
        print("Telemetry RX error:", e)

    # ---- ALTITUDE CONTROL ----
    error = target_z - current_z

    # PID (position)
    thrust = pid_z.update(error, dt)

    # 🔥 ADD VELOCITY DAMPING
    damping = -3.0 * vz   # critical term

    # combine
    velocity = HOVER + 0.4* thrust +0.2* damping
    velocity = max(0, min(100, velocity))

    # ---- SEND TO MOTORS ----
    send_motor(velocity)

    # ---- DEBUG ----
    print(f"Z: {current_z:.2f} → {target_z:.2f} | Vel: {velocity:.2f}")

    time.sleep(0.01)