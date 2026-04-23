# Final Firmware
## Sensor Fusion



A complete sensor fusion pipeline for UAV/drone navigation combining IMU, magnetometer, barometer, and GPS data into a 16-state output vector using complementary filters.

---

### Hardware

| Sensor | Interface | Measures |
|---|---|---|
| MPU-6050 | I²C (0x68) | Accelerometer (ax, ay, az) + Gyroscope (gx, gy, gz) |
| HMC5883L | I²C (0x1E) | Magnetometer (mx, my, mz) |
| BMP280 | I²C/SPI | Barometric pressure + Temperature |
| NEO-6M | UART 9600 | GPS position, velocity, fix quality |

---

### Pipeline Overview

<img width="4359" height="2076" alt="Firmware-NAVIGATION drawio" src="https://github.com/user-attachments/assets/ce30cd6c-e409-4eca-a381-6e4e7ba3e061" />

---

### Stage 1 — Raw to Physical Units

#### 1.1 Accelerometer (MPU-6050)

$$a_x = \frac{a_x^{\text{raw}}}{16384}, \quad a_y = \frac{a_y^{\text{raw}}}{16384}, \quad a_z = \frac{a_z^{\text{raw}}}{16384} \quad [\text{g}]$$

Multiply by 9.81 to convert to m/s².

| Full-Scale | Divide by |
|:---:|:---:|
| ±2 g | 16384 |
| ±4 g | 8192 |
| ±8 g | 4096 |
| ±16 g | 2048 |

#### 1.2 Gyroscope (MPU-6050)

$$g_x = \frac{g_x^{\text{raw}}}{131}, \quad g_y = \frac{g_y^{\text{raw}}}{131}, \quad g_z = \frac{g_z^{\text{raw}}}{131} \quad [°/\text{s}]$$

| Full-Scale | Divide by |
|:---:|:---:|
| ±250 °/s | 131.0 |
| ±500 °/s | 65.5 |
| ±1000 °/s | 32.8 |
| ±2000 °/s | 16.4 |

#### 1.3 Magnetometer (HMC5883L)

$$m_x = \frac{m_x^{\text{raw}}}{1090}, \quad m_y = \frac{m_y^{\text{raw}}}{1090}, \quad m_z = \frac{m_z^{\text{raw}}}{1090} \quad [\text{Ga}]$$

Multiply by 100 to convert to µT.

| Range | Divide by |
|:---:|:---:|
| ±0.88 Ga | 1370 |
| ±1.3 Ga | 1090 |
| ±1.9 Ga | 820 |
| ±2.5 Ga | 660 |

#### 1.4 Barometer (BMP280)

No manual math required. Use the library directly:

```cpp
float T = bmp.readTemperature();  // °C
float P = bmp.readPressure();     // Pa
```

#### 1.5 GPS (NEO-6M via TinyGPS++)

```cpp
float Lat     = gps.location.lat();      // decimal degrees, north positive
float Lon     = gps.location.lng();      // decimal degrees, east positive
float Alt_gps = gps.altitude.meters();  // metres AMSL
int   Sats    = gps.satellites.value(); // satellite count
float HDOP    = gps.hdop.hdop();        // dimensionless

float V_gps      = gps.speed.mps();    // total ground speed [m/s]
float psi_gps    = gps.course.deg();   // course from true north [°]
```

**Fix quality mapping:**

```cpp
int Fix;
if      (!gps.location.isValid())     Fix = 0; // no fix
else if (Sats < 4 || HDOP > 5.0)     Fix = 1; // unreliable
else if (Sats < 6 || HDOP > 2.0)     Fix = 2; // marginal
else                                   Fix = 3; // good — use for fusion
```

| Fix | Satellites | HDOP | Use for fusion? |
|:---:|:---:|:---:|:---:|
| 0 | any | any | No |
| 1 | < 4 | > 5.0 | No |
| 2 | 4–5 | 2.0–5.0 | Caution |
| 3 | ≥ 6 | < 2.0 | Yes |

**Recommended GPS quality:**

| Parameter | Minimum | Good | Excellent |
|:---:|:---:|:---:|:---:|
| Satellites | 4 | 6 | 8+ |
| HDOP | < 5.0 | < 2.0 | < 1.0 |

**Velocity decomposition into NED:**

$$V_{n,\text{gps}} = V_{\text{gps}} \cos(\psi_{\text{gps}}), \quad V_{e,\text{gps}} = V_{\text{gps}} \sin(\psi_{\text{gps}}) \quad [\text{m/s}]$$

**Vertical velocity from successive altitude readings:**

$$V_{z,\text{gps}} = \frac{Alt_{\text{gps}}(t) - Alt_{\text{gps}}(t-1)}{dt} \quad [\text{m/s, positive up}]$$

> Only use when Fix = 3.

---

### Stage 2 — Pre-processing

#### 2.1 Barometric Altitude

$$Alt_{\text{baro}} = 44330 \times \left(1 - \left(\frac{P}{101325}\right)^{0.1903}\right) \quad [\text{m}]$$

$$\text{BaroRate} = \frac{Alt_{\text{baro}}(t) - Alt_{\text{baro}}(t-1)}{dt} \quad [\text{m/s}]$$

#### 2.2 Gravity Removal + NED Rotation

Using current roll φ, pitch θ, yaw ψ estimates (fed back from the attitude filters):

$$
R_{body}^{NED} =
\begin{bmatrix}
\cos\theta\cos\psi & \sin\phi\sin\theta\cos\psi - \cos\phi\sin\psi & \cos\phi\sin\theta\cos\psi + \sin\phi\sin\psi \\
\cos\theta\sin\psi & \sin\phi\sin\theta\sin\psi + \cos\phi\cos\psi & \cos\phi\sin\theta\sin\psi - \sin\phi\cos\psi \\
-\sin\theta        & \sin\phi\cos\theta                             & \cos\phi\cos\theta
\end{bmatrix}
$$

Remove gravity from body-frame Z before rotating:

$$
\begin{bmatrix} a_x' \\ a_y' \\ a_z' \end{bmatrix} =
\begin{bmatrix} a_x \\ a_y \\ a_z - 9.81 \end{bmatrix}
$$

Apply rotation:

$$
\begin{bmatrix} a_n \\ a_e \\ a_{\text{up}} \end{bmatrix} =
R_{body}^{NED}
\begin{bmatrix} a_x' \\ a_y' \\ a_z' \end{bmatrix}
$$

> Outputs: aₙ, aₑ, a_up in m/s². Gravity (9.81 m/s²) is subtracted from az before rotation so only true acceleration reaches the NED frame.

---

### Stage 3 — Complementary Filters (16 Outputs)

This stage fuses high-frequency IMU data with low-frequency reference sensors for drift-free state estimation.

---

#### 3.1 Attitude (Filters 1–3)

**Tuning:** $\alpha = 0.98$ (Range: 0.95 – 0.99). High $\alpha$ favors gyro smoothness; low $\alpha$ favors faster correction.

**Filter 1 — Roll ($\phi$)**

Predict roll by adding gyroscope change to the previous state.

$$\phi_{\text{gyro}} = \phi_{n-1} + g_x \cdot dt$$

Calculate roll reference using the accelerometer gravity vector.

$$\phi_{\text{acc}} = \arctan2(a_y, a_z)$$

Fuse both values to eliminate gyro drift.

$$\mathbf{\phi_n = \alpha \cdot \phi_{\text{gyro}} + (1 - \alpha) \cdot \phi_{\text{acc}}}$$

**Filter 2 — Pitch ($\theta$)**

Predict pitch by integrating the Y-axis gyroscope rate.

$$\theta_{\text{gyro}} = \theta_{n-1} + g_y \cdot dt$$

Calculate pitch reference from the accelerometer tilt.

$$\theta_{\text{acc}} = \arctan2\!\left(-a_x, \sqrt{a_y^2 + a_z^2}\right)$$

Fuse both values for a stable pitch estimate.

$$\mathbf{\theta_n = \alpha \cdot \theta_{\text{gyro}} + (1 - \alpha) \cdot \theta_{\text{acc}}}$$

**Filter 3 — Yaw ($\psi$)**

Predict heading using Z-axis gyroscope integration.

$$\psi_{\text{gyro}} = \psi_{\text{n-1}} + g_z \cdot dt$$

Calculate tilt-compensated north using the magnetometer and current attitude.

$$X_h = m_x\cos\theta + m_z\sin\theta$$

$$Y_h = m_x\sin\phi\sin\theta + m_y\cos\phi - m_z\sin\phi\cos\theta$$

$$\psi_{\text{mag}} = \arctan2(-Y_h,\, X_h)$$

Fuse both values to align heading with magnetic north.

$$\mathbf{\psi_n = \alpha \cdot \psi_{\text{gyro}} + (1 - \alpha) \cdot \psi_{\text{mag}}}$$

> **Note:** Wrap $\psi$ to $[-\pi, +\pi]$ after update.

---

#### 3.2 Body Rates (Filters 4–6)

Calibrated gyroscope data passed through for low-latency control.

$$\omega_x = g_x \text{ [°/s]}$$

$$\omega_y = g_y \text{ [°/s]}$$

$$\omega_z = g_z \text{ [°/s]}$$

---

#### 3.3 Global Position (Filters 7–9)

**Filter 7 & 8 — Latitude & Longitude**

Update coordinates only during a valid GPS fix; otherwise, hold last position.

$$\text{Lat}_n = \begin{cases} \text{Lat}_{\text{gps}} & \text{Fix} \geq 3 \\\\ \text{Lat}_{n-1} & \text{otherwise} \end{cases}$$

$$\text{Lon}_n = \begin{cases} \text{Lon}_{\text{gps}} & \text{Fix} \geq 3 \\\\ \text{Lon}_{n-1} & \text{otherwise} \end{cases}$$

**Filter 9 — Altitude**

Predict height by adding vertical movement to the last altitude.

$$Alt_{\text{pred}} = Alt_{n-1} + V_{\text{alt}} \cdot dt$$

Select altitude reference based on GPS fix quality.

$$Alt_{\text{ref}} = \begin{cases} Alt_{\text{gps}} & \text{Fix} \geq 3 \\\\ Alt_{\text{baro}} & \text{otherwise} \end{cases}$$

Fuse prediction with reference for stable altitude.

$$\mathbf{Alt_n = \alpha \cdot Alt_{\text{pred}} + (1 - \alpha) \cdot Alt_{\text{ref}}}$$

---

#### 3.4 Velocities (Filters 10–12)

**Filter 10 & 11 — Velocity North/East**

Predict horizontal speed by integrating NED acceleration.

$$V_{n/e,\text{pred}} = V_{n/e,n-1} + a_{n/e} \cdot dt$$

Obtain absolute speed reference from GPS.

$$V_{n/e,\text{ref}} = \begin{cases} V_{n/e,\text{gps}} & \text{Fix} \geq 3 \\\\ 0 & \text{otherwise} \end{cases}$$

Fuse integration with GPS to stop velocity drift.

$$\mathbf{V_{n/e,n} = \alpha \cdot V_{n/e,\text{pred}} + (1 - \alpha) \cdot V_{n/e,\text{ref}}}$$

**Filter 12 — Velocity Altitude**

Predict climb rate using vertical acceleration.

$$V_{\text{alt,pred}} = V_{\text{alt},n-1} + a_{\text{up}} \cdot dt$$

Blend Barometric and GPS rates for a robust reference.

$$V_{\text{ref}} = \begin{cases} 0.7 \cdot \text{BaroRate} + 0.3 \cdot V_{z,\text{gps}} & \text{Fix} \geq 3 \\\\ \text{BaroRate} & \text{otherwise} \end{cases}$$

Set damping factor based on altitude to ignore ground-effect noise.

$$\alpha = \begin{cases} 0.999 & Alt < 0.8\text{m} \\\\ 0.98 & \text{otherwise} \end{cases}$$

Finalize vertical velocity state via fusion.

$$\mathbf{V_{\text{alt},n} = \alpha \cdot V_{\text{alt,pred}} + (1 - \alpha) \cdot V_{\text{ref}}}$$

---

#### 3.5 Metadata (Filters 13–16)

Raw diagnostic data for system health monitoring.

| Filter | Output | Source | Units |
| :--- | :--- | :--- | :--- |
| **13** | Temperature | BMP280 | °C |
| **14** | Satellite Count | NEO-6M | — |
| **15** | HDOP | NEO-6M | — |
| **16** | Fix Type | NEO-6M | 0–3 |

---

### Output State Vector

| # | Variable | Unit | Description |
|:---:|---|:---:|---|
| 1 | φ (Roll) | rad | Rotation about X axis |
| 2 | θ (Pitch) | rad | Rotation about Y axis |
| 3 | ψ (Yaw) | rad | Rotation about Z axis |
| 4 | ωx (Roll Rate) | °/s | Body angular rate (X) |
| 5 | ωy (Pitch Rate) | °/s | Body angular rate (Y) |
| 6 | ωz (Yaw Rate) | °/s | Body angular rate (Z) |
| 7 | Latitude | ° | Decimal degrees (North+) |
| 8 | Longitude | ° | Decimal degrees (East+) |
| 9 | Altitude | m | Meters above MSL |
| 10 | Velocity North | m/s | NED North component |
| 11 | Velocity East | m/s | NED East component |
| 12 | Velocity Alt | m/s | Vertical rate (Up+) |
| 13 | Temperature | °C | Sensor temperature |
| 14 | Satellites | — | Active GPS satellites |
| 15 | HDOP | — | Precision dilution |
| 16 | GPS Fix | — | Fix quality (0–3) |

---

### Filter Tuning Reference

| Parameter | Value | Meaning |
|:---:|:---:|---|
| Attitude α | 0.98 | % trust in gyro integration |
| Velocity α | 0.95 | % trust in IMU dead-reckoning |
| Altitude α | 0.99 | % trust in integrated velocity |
| Bubble filter α| 0.999 | Ground damping (Alt < 0.8m) |

## Control
<img width="3936" height="1266" alt="Firmware-CONTROL drawio" src="https://github.com/user-attachments/assets/06672eb3-31ba-4b80-9e56-0da810da8fb0" />
