import math

class Navigation:
    def __init__(self):
        # Constants
        self.P0 = 101325
        self.ACCEL_SCALE = 9.80665 / 16384.0
        self.GYRO_SCALE = (math.pi / 180) / 131.0
        self.ALPHA_RPY = 0.98
        self.ALPHA_ALT = 0.95

        # Sensor orientation offsets (degrees)
        self.orientation_angles = {
            'mpu6050': 15,
            'mag': 10,
            'baro': 0,
            'gps': 0
        }

        # Persistent state: roll, pitch, yaw (rad), alt (m)
        self.prev_state = [0.0, 0.0, 0.0, 0.0]

    def rotate_z(self, vec, angle_deg):
        angle_rad = math.radians(angle_deg)
        x, y, z = vec
        x_new = x * math.cos(angle_rad) - y * math.sin(angle_rad)
        y_new = x * math.sin(angle_rad) + y * math.cos(angle_rad)
        return [x_new, y_new, z]

    def average(self, vectors):
        n = len(vectors)
        return [sum(v[i] for v in vectors) / n for i in range(len(vectors[0]))]

    def process(self, mpu6050_list, gps_list, mag_list, baro_list):
        """
        Inputs:
            mpu6050_list: [[ax, ay, az, gx, gy, gz], ...]
            gps_list    : [[lat, lon, alt], ...]
            mag_list    : [[mx, my, mz], ...]
            baro_list   : [[pressure, temp, humidity], ...]

        Output:
            [lat, lon, alt, roll_deg, pitch_deg, yaw_deg]
        """

        prev_roll, prev_pitch, prev_yaw, prev_alt = self.prev_state

        # 1. Rotate and scale MPU6050 data
        acc_list, gyro_list = [], []
        for v in mpu6050_list:
            acc_raw = [v[i] * self.ACCEL_SCALE for i in range(3)]
            gyro_raw = [v[i] * self.GYRO_SCALE for i in range(3, 6)]
            acc_rot = self.rotate_z(acc_raw, self.orientation_angles['mpu6050'])
            gyro_rot = self.rotate_z(gyro_raw, self.orientation_angles['mpu6050'])
            acc_list.append(acc_rot)
            gyro_list.append(gyro_rot)

        # 2. Rotate other sensors
        mag_rot_list = [self.rotate_z(m, self.orientation_angles['mag']) for m in mag_list]

        # 3. Average all sensors
        acc_avg = self.average(acc_list)
        gyro_avg = self.average(gyro_list)
        mag_avg = self.average(mag_rot_list)
        gps_avg = self.average(gps_list)
        baro_avg = self.average(baro_list)

        # 4. Compute roll, pitch from accelerometer
        acc_roll = math.atan2(acc_avg[1], acc_avg[2])
        acc_pitch = math.atan2(-acc_avg[0], math.sqrt(acc_avg[1]**2 + acc_avg[2]**2))

        # 5. Compute yaw from magnetometer
        mag_x = mag_avg[0] * math.cos(acc_pitch) + mag_avg[2] * math.sin(acc_pitch)
        mag_y = (mag_avg[0] * math.sin(acc_roll) * math.sin(acc_pitch) +
                 mag_avg[1] * math.cos(acc_roll) -
                 mag_avg[2] * math.sin(acc_roll) * math.cos(acc_pitch))
        mag_yaw = math.atan2(-mag_y, mag_x)

        # 6. Altitude from baro + GPS
        pressure = baro_avg[0]
        gps_alt = gps_avg[2]
        alt_baro = 44330 * (1 - (pressure / self.P0) ** 0.1903)

        # 7. Complementary filter
        roll = self.ALPHA_RPY * (prev_roll + gyro_avg[0]) + (1 - self.ALPHA_RPY) * acc_roll
        pitch = self.ALPHA_RPY * (prev_pitch + gyro_avg[1]) + (1 - self.ALPHA_RPY) * acc_pitch
        yaw = self.ALPHA_RPY * (prev_yaw + gyro_avg[2]) + (1 - self.ALPHA_RPY) * mag_yaw
        alt = self.ALPHA_ALT * alt_baro + (1 - self.ALPHA_ALT) * gps_alt

        # 8. Update internal state
        self.prev_state = [roll, pitch, yaw, alt]

        # 9. Return final fused values
        return [
            gps_avg[0],               # latitude
            gps_avg[1],               # longitude
            alt,                      # altitude (fused)
            math.degrees(roll),       # roll in degrees
            math.degrees(pitch),      # pitch in degrees
            math.degrees(yaw)         # yaw in degrees
        ]
