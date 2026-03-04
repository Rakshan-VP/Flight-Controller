import time
import math

class Control:
    def __init__(self):
        self.prev_time = time.time()

        # Limits
        self.max_roll_deg = 30.0
        self.max_pitch_deg = 30.0
        self.max_yaw_rate_deg = 5.0  # deg/s
        self.alt_limit = (0.0, 1.0)  # throttle [0–1]

        # PID state
        self.roll_integral = 0.0
        self.pitch_integral = 0.0
        self.yaw_integral = 0.0
        self.alt_integral = 0.0

        self.prev_roll_error = 0.0
        self.prev_pitch_error = 0.0
        self.prev_yaw_error = 0.0
        self.prev_alt_error = 0.0

        self.prev_roll_derivative = 0.0
        self.prev_pitch_derivative = 0.0
        self.prev_yaw_derivative = 0.0
        self.prev_alt_derivative = 0.0

        # PID gains (Kp, Ki, Kd)
        self.roll_gains = (1.0, 0.0, 0.2)
        self.pitch_gains = (1.0, 0.0, 0.2)
        self.yaw_gains = (1.5, 0.0, 0.3)
        self.alt_gains = (1.0, 0.05, 0.2)

        self.filter_tau = 0.02  # Low-pass filter time constant

    def _dt(self):
        now = time.time()
        dt = now - self.prev_time
        self.prev_time = now
        return max(dt, 1e-3)

    def _pid(self, error, prev_error, integral, prev_derivative, gains, limits, dt):
        kp, ki, kd = gains
        integral += error * dt

        derivative = (error - prev_error) / dt
        derivative = prev_derivative + self.filter_tau / (self.filter_tau + dt) * (derivative - prev_derivative)

        output = kp * error + ki * integral + kd * derivative
        output = max(limits[0], min(limits[1], output))  # Clamp

        return output, integral, derivative

    def process(self, nav_state, guidance_out):
        _, _, curr_alt, curr_roll, curr_pitch, curr_yaw = nav_state
        mode = guidance_out["mode"]
        dt = self._dt()

        # Errors
        roll_err = guidance_out["desired_roll"] - curr_roll
        pitch_err = guidance_out["desired_pitch"] - curr_pitch
        yaw_err = guidance_out["desired_yaw"] - curr_yaw
        alt_err = guidance_out["desired_thrust"] - curr_alt

        # PID Controllers
        roll_cmd, self.roll_integral, self.prev_roll_derivative = self._pid(
            roll_err, self.prev_roll_error, self.roll_integral, self.prev_roll_derivative,
            self.roll_gains, (-self.max_roll_deg, self.max_roll_deg), dt
        )
        self.prev_roll_error = roll_err

        pitch_cmd, self.pitch_integral, self.prev_pitch_derivative = self._pid(
            pitch_err, self.prev_pitch_error, self.pitch_integral, self.prev_pitch_derivative,
            self.pitch_gains, (-self.max_pitch_deg, self.max_pitch_deg), dt
        )
        self.prev_pitch_error = pitch_err

        yaw_cmd, self.yaw_integral, self.prev_yaw_derivative = self._pid(
            yaw_err, self.prev_yaw_error, self.yaw_integral, self.prev_yaw_derivative,
            self.yaw_gains, (-self.max_yaw_rate_deg, self.max_yaw_rate_deg), dt
        )
        self.prev_yaw_error = yaw_err

        # Altitude: If Stabilize, use throttle directly
        if mode == "Stabilize":
            thrust = guidance_out["desired_thrust"]
        else:
            thrust, self.alt_integral, self.prev_alt_derivative = self._pid(
                alt_err, self.prev_alt_error, self.alt_integral, self.prev_alt_derivative,
                self.alt_gains, self.alt_limit, dt
            )
            self.prev_alt_error = alt_err

        # Convert to PWM
        def to_pwm(val, max_val):
            return int(1500 + (val / max_val) * 500)

        roll_pwm = to_pwm(roll_cmd, self.max_roll_deg)
        pitch_pwm = to_pwm(pitch_cmd, self.max_pitch_deg)
        yaw_pwm = to_pwm(yaw_cmd, self.max_yaw_rate_deg)
        thrust_pwm = int(1000 + thrust * 1000)

        roll_pwm = max(1000, min(2000, roll_pwm))
        pitch_pwm = max(1000, min(2000, pitch_pwm))
        yaw_pwm = max(1000, min(2000, yaw_pwm))
        thrust_pwm = max(1000, min(2000, thrust_pwm))

        # Motor mixing (X quad)
        m1 = thrust_pwm - pitch_cmd + roll_cmd + yaw_cmd  # Front left (CW)
        m2 = thrust_pwm - pitch_cmd - roll_cmd - yaw_cmd  # Front right (CCW)
        m3 = thrust_pwm + pitch_cmd - roll_cmd + yaw_cmd  # Rear right (CW)
        m4 = thrust_pwm + pitch_cmd + roll_cmd - yaw_cmd  # Rear left (CCW)

        def clamp_pwm(x): return int(max(1000, min(2000, x)))

        motor_pwms = {
            "M1": clamp_pwm(m1),
            "M2": clamp_pwm(m2),
            "M3": clamp_pwm(m3),
            "M4": clamp_pwm(m4)
        }

        return {
            "roll_pwm": roll_pwm,
            "pitch_pwm": pitch_pwm,
            "yaw_pwm": yaw_pwm,
            "thrust_pwm": thrust_pwm,
            "motors": motor_pwms
        }
