from controller import Supervisor
import math
import socket
import json
import base64
import numpy as np
import cv2  # Required for JPEG compression

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

# Camera
camera = robot.getDevice("chasecam")
camera.enable(timestep)

cam_width = camera.getWidth()
cam_height = camera.getHeight()

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

    r, p, yaw = imu.getRollPitchYaw()
    r_deg = math.degrees(r)
    p_deg = math.degrees(p)
    yaw_deg = math.degrees(yaw)

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
# TIME CONTROL INIT
# =========================
start_time = robot.getTime()

# =========================
# CAMERA CONTROL
# =========================
frame_skip = 1
frame_count = 0

# =========================
# MAIN LOOP
# =========================
while robot.step(timestep) != -1:

    current_time = robot.getTime() - start_time

    # =========================
    # MOTOR CONTROL
    # =========================
    if current_time < 2.0:
        cmd = [51, 51, 51, 51]
    elif current_time > 2.0:
        cmd = [51.5, 51.25, 51.5, 51.25]
    else:
        try:
            data, _ = sock_rx.recvfrom(1024)
            cmd = json.loads(data.decode())
        except (BlockingIOError, Exception):
            cmd = None

    if cmd and len(cmd) == 4:
        tau_z = 0.0
        for i, m in enumerate(motors):
            w = clamp(cmd[i], 0, 100)
            m.setVelocity(w)
            if i % 2 == 0:
                tau_z += k * w**2
            else:
                tau_z -= k * w**2

        vel = node.getVelocity()
        wz = vel[5]
        alpha_z = tau_z / Izz
        new_wz = wz + alpha_z * dt
        node.setVelocity([vel[0], vel[1], vel[2], vel[3], vel[4], new_wz])

    # =========================
    # CAMERA CAPTURE (OPTIMIZED FOR MOTION)
    # =========================
    frame_count += 1
    if frame_count % frame_skip == 0:
        try:
            image = camera.getImage()
            if image:
                img_np = np.frombuffer(image, dtype=np.uint8).reshape((cam_height, cam_width, 4))
                color_img = img_np[:, :, :3] 

                # INCREASE QUALITY: 95 provides near-lossless color for moving parts
                _, buffer = cv2.imencode('.jpg', color_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

                img_b64 = base64.b64encode(buffer).decode('utf-8')
                cam_packet = {
                    "w": cam_width,
                    "h": cam_height,
                    "img": img_b64
                }
                sock_tx.sendto(json.dumps(cam_packet).encode(), (UDP_IP, 9004))

        except Exception as e:
            print(f"Camera TX error: {e}")

    # =========================
    # SEND TELEMETRY
    # =========================
    try:
        telemetry = get_telemetry()
        msg = json.dumps(telemetry)
        sock_tx.sendto(msg.encode(), (UDP_IP, 9002))
    except Exception as e:
        print(f"Telemetry TX error: {e}")