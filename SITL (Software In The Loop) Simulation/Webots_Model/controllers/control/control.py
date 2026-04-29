from controller import Supervisor
import math
import socket
import json

# =========================
# INIT ROBOT
# =========================
robot = Supervisor()
timestep = int(robot.getBasicTimeStep())
dt = timestep / 1000.0

# Motors
m1 = robot.getDevice("M1FL")
m2 = robot.getDevice("M2FR")
m3 = robot.getDevice("M3BR")
m4 = robot.getDevice("M4BL")

motors = [m1, m2, m3, m4]

for m in motors:
    m.setPosition(float('inf'))
    m.setVelocity(0.0)

# Sensors
gps = robot.getDevice("gps")
imu = robot.getDevice("imu")
gyro = robot.getDevice("gyro")

gps.enable(timestep)
imu.enable(timestep)
gyro.enable(timestep)

# Self node
node = robot.getSelf()

# =========================
# UDP SETUP
# =========================
UDP_IP = "127.0.0.1"

sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_rx.bind((UDP_IP, 9003))
sock_rx.setblocking(False)

# =========================
# HELPERS
# =========================
def fmt(v, eps=1e-2):
    return 0.0 if abs(v) < eps else v

def clamp(v, vmin, vmax):
    return max(vmin, min(vmax, v))

def get_telemetry():
    x, y, z = gps.getValues()

    vel = node.getVelocity()
    xdot, ydot, zdot = vel[0], vel[1], vel[2]

    # Webots returns radians: convert to degrees
    r, p, yaw = imu.getRollPitchYaw()
    r_deg = math.degrees(r)
    p_deg = math.degrees(p)
    yaw_deg = math.degrees(yaw)

    # Webots returns rad/s: convert to deg/s
    rdot, pdot, ydot_ang = gyro.getValues()
    rdot_deg = math.degrees(rdot)
    pdot_deg = math.degrees(pdot)
    ydot_ang_deg = math.degrees(ydot_ang)

    return [
        x, y, z,
        xdot, ydot, zdot,
        r_deg, p_deg, yaw_deg,
        rdot_deg, pdot_deg, ydot_ang_deg
    ]

# =========================
# PHYSICS CONSTANTS
# =========================
k = 5e-5
Izz = (1/12) * 1.0 * (0.5**2 + 0.5**2)

# =========================
# MAIN LOOP
# =========================
while robot.step(timestep) != -1:

    # ---- RECEIVE + APPLY + YAW ----
    try:
        data, _ = sock_rx.recvfrom(1024)
        cmd = json.loads(data.decode())

        if len(cmd) == 4:

            tau_z = 0.0

            for i, m in enumerate(motors):
                w = clamp(cmd[i], 0, 100)
                m.setVelocity(w)

                # yaw torque contribution
                if i % 2 == 0:   # m1, m3
                    tau_z += k * w**2
                else:            # m2, m4
                    tau_z -= k * w**2

            # apply yaw dynamics
            vel = node.getVelocity()
            wz = vel[5]

            alpha_z = tau_z / Izz
            new_wz = wz + alpha_z * dt

            node.setVelocity([
                vel[0], vel[1], vel[2],
                vel[3], vel[4], new_wz
            ])

    except BlockingIOError:
        pass
    except Exception as e:
        print("RX error:", e)

    # ---- SEND TELEMETRY ----
    try:
        telemetry = get_telemetry()

        # unpack
        x, y, z, vx, vy, vz, r, p, yaw, wx, wy, wz = telemetry

        # format (zero small values)
        x, y, z   = fmt(x), fmt(y), fmt(z)
        vx, vy, vz = fmt(vx), fmt(vy), fmt(vz)
        r, p, yaw = fmt(r), fmt(p), fmt(yaw)
        wx, wy, wz = fmt(wx), fmt(wy), fmt(wz)

        # 🔥 single-line clean print
        print(
            f"x:{x:.2f} | y:{y:.2f} | z:{z:.2f} | "
            f"vx:{vx:.2f} | vy:{vy:.2f} | vz:{vz:.2f} | "
            f"r:{r:.2f} | p:{p:.2f} | yaw:{yaw:.2f} | "
            f"wx:{wx:.2f} | wy:{wy:.2f} | wz:{wz:.2f}"
        )

        # still send over UDP
        msg = json.dumps(telemetry)
        sock_tx.sendto(msg.encode(), (UDP_IP, 9002))

    except Exception as e:
        print("TX error:", e)