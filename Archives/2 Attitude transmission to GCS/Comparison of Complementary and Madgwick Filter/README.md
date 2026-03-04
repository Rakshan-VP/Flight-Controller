# 🧭 Comparison of Complementary and Madgwick Filter

## 🎯 Objective
This project compares the **Complementary Filter** and the **Madgwick Filter** for attitude estimation (roll and pitch) using two **MPU6050 IMUs**.  
Both filters fuse accelerometer and gyroscope data but differ in how they correct and stabilize orientation estimates.

---

## ⚙️ Hardware Used
- STM32 (or Arduino-compatible board with two I²C ports)  
- 2 × MPU6050 IMU sensors  
- nRF24L01 RF transceiver modules (for wireless data transfer)  
- Host computer running the **GCS (Ground Control Station)** to log data  

---

## 🧩 File Descriptions

### 🔹 fc.ino — Flight Controller Side
- Initializes **two IMUs** (`imu1`, `imu2`) using separate I²C buses.  
- Implements:
  - Complementary Filter for each IMU  
  - Madgwick Filter for each IMU  
- Combines both IMUs’ outputs by averaging roll and pitch.  
- Sends the telemetry (roll/pitch from both filters) via **nRF24L01** to the ground station.

**Telemetry Packet Structure:**

| Field | Description |
|-------|--------------|
| `roll_cf` | Roll angle from Complementary Filter (°) |
| `pitch_cf` | Pitch angle from Complementary Filter (°) |
| `roll_mad` | Roll angle from Madgwick Filter (°) |
| `pitch_mad` | Pitch angle from Madgwick Filter (°) |

---

### 🔹 gcs.ino — Ground Control Station Side
- Receives telemetry data wirelessly via **nRF24L01**.  
- Outputs the data over Serial in **CSV format**:

```
roll_cf,roll_mad,pitch_cf,pitch_mad
-1.23,-1.17,0.54,0.59
...
```

- You can save this serial output directly as a `.csv` file for plotting and comparison in MATLAB, Python, or Excel.

---

## 🧮 Mathematical Background

### 1. Complementary Filter

The **complementary filter** linearly combines accelerometer and gyroscope data:

roll_est = α * (roll_prev + gyro_roll_rate * Δt) + (1 - α) * roll_acc

pitch_est = α * (pitch_prev + gyro_pitch_rate * Δt) + (1 - α) * pitch_acc

where:  
- α = 0.98 → weight given to gyroscope integration  
- (1 − α) = 0.02 → weight given to accelerometer correction  
- Δt = time interval between updates  

It’s a **first-order low-pass/high-pass filter pair**:
- Gyroscope → High-pass (good for short-term stability)  
- Accelerometer → Low-pass (good for long-term drift correction)

---

### 2. Madgwick Filter

The **Madgwick filter** is a quaternion-based orientation estimator that uses a **gradient descent optimization** to minimize the error between the measured and estimated direction of gravity.

#### Key equations:

1. **Quaternion update (simplified form):**
   
 q_dot = 0.5 * q ⊗ ω - β * gradient(f(q, a))
 
 where:  
- q = current quaternion  
- ω = gyroscope angular velocity  
- gradient(f(q, a)) = gradient of the objective function  
- β = convergence rate

2. **Normalization:**
 After each update, \( q \) is normalized:
 q = q / ||q||

3. **Conversion to Euler angles:**
   
 roll = atan2(2*(qwqx + qyqz), 1 - 2*(qx^2 + qy^2))
 
 pitch = asin(2*(qwqy - qzqx))

The Madgwick algorithm provides **better accuracy and faster convergence**, especially when gyroscope bias or sensor noise are present.

---

## 📊 Comparison Table

| Feature | Complementary Filter | Madgwick Filter |
|----------|----------------------|-----------------|
| **Computation Type** | Simple arithmetic | Quaternion + gradient descent |
| **Math Basis** | Linear filtering | Nonlinear optimization |
| **Computational Load** | Very low | Moderate |
| **Drift Handling** | Partial (slow drift correction) | Excellent (full quaternion normalization) |
| **Response Speed** | Fast | Fast, but smoother |
| **Accuracy** | Good for low-cost IMUs | High accuracy, even in dynamic motion |
| **Tuning Parameter** | α (0–1) | β (gain, typically 0.1–1.0) |
| **Gyro Bias Compensation** | No | Yes |
| **Best Use Case** | Simple, low-power systems | Precision orientation tracking (drones, VR) |

