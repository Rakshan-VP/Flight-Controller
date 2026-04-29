from controller import Supervisor  # ← not Robot

robot = Supervisor()               # ← not Robot()
timestep = int(robot.getBasicTimeStep())

m1 = robot.getDevice("M1FL")
m2 = robot.getDevice("M2FR")
m3 = robot.getDevice("M3BR")
m4 = robot.getDevice("M4BL")

for m in [m1, m2, m3, m4]:
    m.setPosition(float('inf'))

HOVER = 51.0
m1.setVelocity(HOVER)
m2.setVelocity(HOVER)
m3.setVelocity(HOVER)
m4.setVelocity(HOVER)

self_node = robot.getSelf()        # ← works now

k = 5e-5
w1, w2, w3, w4 = 51, 53, 51, 53
tau_z = (+ k * w1**2
         - k * w2**2
         + k * w3**2
         - k * w4**2)

Izz = (1/12) * 1.0 * (0.5**2 + 0.5**2)
dt = timestep / 1000.0

while robot.step(timestep) != -1:
    vel = self_node.getVelocity()
    alpha_z = tau_z / Izz
    new_wz = vel[5] + alpha_z * dt

    self_node.setVelocity([vel[0], vel[1], vel[2],
                           vel[3], vel[4], new_wz])

    print(f"tau={tau_z:.5f}  wz={new_wz:.4f} rad/s")