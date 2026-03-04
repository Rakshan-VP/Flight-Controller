import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
file = "3 Level Test/log/20260304_181729.csv"
data = pd.read_csv(file)

t = data["t"]

roll = data["roll"]
pitch = data["pitch"]

m1 = data["m1"]
m2 = data["m2"]
m3 = data["m3"]
m4 = data["m4"]

# Target level angle
roll_setpoint = 0
pitch_setpoint = 0

roll_error = roll_setpoint - roll
pitch_error = pitch_setpoint - pitch


# -------- Plot 1 : Roll & Pitch vs Time --------
plt.figure()

plt.plot(t, roll, label="Roll")
plt.plot(t, pitch, label="Pitch")

plt.xlabel("Time (s)")
plt.ylabel("Angle (deg)")
plt.title("Roll & Pitch vs Time")
plt.legend()
plt.grid()


# -------- Plot 2 : Error vs Time --------
plt.figure()

plt.plot(t, roll_error, label="Roll Error")
plt.plot(t, pitch_error, label="Pitch Error")

plt.xlabel("Time (s)")
plt.ylabel("Error (deg)")
plt.title("Roll & Pitch Error vs Time")
plt.legend()
plt.grid()


# -------- Plot 3 : Motor PWM --------
plt.figure()

plt.plot(t, m1, label="M1")
plt.plot(t, m2, label="M2")
plt.plot(t, m3, label="M3")
plt.plot(t, m4, label="M4")

plt.xlabel("Time (s)")
plt.ylabel("PWM")
plt.title("Motor Outputs vs Time")
plt.legend()
plt.grid()

plt.show()