import time
import math

class Guidance:
    def __init__(self):
        # Limits
        self.max_roll_deg = 30.0
        self.max_pitch_deg = 30.0
        self.max_yaw_rate_deg = 5.0
        self.max_climb_rate = 2.0     # m/s
        self.max_descent_rate = -1.5  # m/s

        # State
        self.current_mode = None
        self.last_state = None
        self.rc_input_pwm = None

        self.prev_time = None
        self.target_altitude = None

        # Position Hold & RTL
        self.hold_position = None
        self.home_position = None
        self.home_buffer = []
        self.home_set = False
        self.rtl_stage = None
        self.rtl_tolerance = 1.0

        # Guided
        self.guided_command = None
        self.guided_target = {}
        self.guided_stage = None

        # Output
        self.guidance_output = self._default_output()

    def _default_output(self):
        return {"desired_roll": 0.0, "desired_pitch": 0.0, "desired_yaw": 0.0, "desired_thrust": 0.0}

    def _set_guidance_output(self, roll=0.0, pitch=0.0, yaw=0.0, thrust=0.0):
        self.guidance_output = {
            "desired_roll": roll,
            "desired_pitch": pitch,
            "desired_yaw": yaw,
            "desired_thrust": thrust
        }
        return self.guidance_output

    def process(self, states, flight_mode, rc_failsafe, battery_failsafe, rc_input_pwm):
        self.last_state = states
        self.rc_input_pwm = rc_input_pwm
        self.current_mode = flight_mode

        self._update_home_position(states)

        if battery_failsafe:
            self.current_mode = 5  # LAND
        elif rc_failsafe:
            self.current_mode = 6  # RTL

        mode_function_map = {
            1: self._stabilize,
            2: self._alt_hold,
            3: self._pos_hold,
            4: self._guided,
            5: self._land,
            6: self._rtl
        }

        mode_name_map = {
            1: "Stabilize",
            2: "AltHold",
            3: "PosHold",
            4: "Guided",
            5: "Land",
            6: "RTL"
        }

        result = mode_function_map.get(self.current_mode, self._stabilize)()
        result["mode"] = mode_name_map.get(self.current_mode, "Stabilize")
        return result

    def _stabilize(self):
        roll, pitch = self._manual_angle_inputs()
        yaw = self._map_pwm_to_rate(self.rc_input_pwm[2], self.max_yaw_rate_deg)
        thrust = self._map_pwm_to_thrust(self.rc_input_pwm[3])
        return self._set_guidance_output(roll, pitch, yaw, thrust)

    def _alt_hold(self):
        self._update_target_altitude()
        roll, pitch, yaw = self._manual_attitude_inputs()
        return self._set_guidance_output(roll, pitch, yaw, self.target_altitude)

    def _pos_hold(self):
        lat, lon, alt, _, _, yaw_deg = self.last_state
        yaw_rad = math.radians(yaw_deg)
        roll_pwm, pitch_pwm, yaw_pwm, _ = self.rc_input_pwm

        manual = abs(roll_pwm - 1500) > 50 or abs(pitch_pwm - 1500) > 50
        yaw = self._map_pwm_to_rate(yaw_pwm, self.max_yaw_rate_deg)

        if manual:
            roll, pitch = self._manual_angle_inputs()
            self.hold_position = (lat, lon)
        else:
            if self.hold_position is None:
                self.hold_position = (lat, lon)
            roll, pitch = self._compute_pos_error(self.hold_position, (lat, lon), lat, yaw_rad)

        self._update_target_altitude()
        return self._set_guidance_output(roll, pitch, yaw, self.target_altitude)

    def _guided(self):
        cmd = self.guided_command
        if cmd == "takeoff": return self._guided_takeoff()
        if cmd == "goto": return self._guided_goto()
        if cmd == "land": return self._land()
        if cmd == "rtl":
            self.current_mode = 6
            return self._rtl()
        return self._failsafe()

    def _land(self):
        self._init_altitude_if_needed()
        self.target_altitude -= 0.5 * self._dt()
        return self._set_guidance_output(0.0, 0.0, 0.0, max(0.0, self.target_altitude))

    def _rtl(self):
        if not self.home_set:
            return self._failsafe()

        lat, lon, alt, _, _, yaw_deg = self.last_state
        home_lat, home_lon = self.home_position
        dx = (home_lat - lat) * 111000.0
        dy = (home_lon - lon) * 111000.0 * math.cos(math.radians(lat))
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if self.rtl_stage is None:
            self.rtl_stage = "goto_home"
            self._init_altitude_if_needed()

        if self.rtl_stage == "goto_home":
            if dist <= self.rtl_tolerance:
                self.rtl_stage = "descend"
                return self._land()
            yaw_rad = math.radians(yaw_deg)
            roll, pitch = self._compute_pos_error((home_lat, home_lon), (lat, lon), lat, yaw_rad)
            return self._set_guidance_output(roll, pitch, 0.0, self.target_altitude)

        elif self.rtl_stage == "descend":
            return self._land()

        return self.guidance_output

    def _failsafe(self):
        return self._set_guidance_output(0.0, 0.0, 0.0, 0.0)

    def set_guided_command(self, command, target=None):
        self.guided_command = command
        self.guided_target = target or {}
        self.guided_stage = None

    def _guided_takeoff(self):
        target_alt = self.guided_target.get("altitude", 5.0)
        self._init_altitude_if_needed()
        dt = self._dt()
        self.target_altitude += 0.8 * dt

        if self.target_altitude >= target_alt:
            self.target_altitude = target_alt
            return self._alt_hold()

        return self._set_guidance_output(0.0, 0.0, 0.0, self.target_altitude)

    def _guided_goto(self):
        if not all(k in self.guided_target for k in ["lat", "lon", "altitude"]):
            return self._failsafe()

        lat, lon, alt, _, _, yaw_deg = self.last_state
        tgt_lat = self.guided_target["lat"]
        tgt_lon = self.guided_target["lon"]
        tgt_alt = self.guided_target["altitude"]

        yaw_rad = math.radians(yaw_deg)
        roll, pitch = self._compute_pos_error((tgt_lat, tgt_lon), (lat, lon), lat, yaw_rad)

        self._init_altitude_if_needed()
        alt_error = tgt_alt - alt
        climb_rate = max(-1.0, min(1.0, alt_error))
        self.target_altitude += climb_rate * self._dt()

        dist = math.sqrt((tgt_lat - lat) ** 2 + (tgt_lon - lon) ** 2) * 111000.0
        if dist < 0.5 and abs(alt_error) < 0.2:
            return self._alt_hold()

        return self._set_guidance_output(roll, pitch, 0.0, self.target_altitude)

    def _update_home_position(self, states):
        lat, lon = states[0], states[1]
        if not self.home_set:
            self.home_buffer.append((lat, lon))
            if len(self.home_buffer) >= 4:
                self.home_position = tuple(sum(x) / len(x) for x in zip(*self.home_buffer))
                self.home_set = True

    def _manual_angle_inputs(self):
        roll = self._map_pwm_to_angle(self.rc_input_pwm[0], self.max_roll_deg)
        pitch = self._map_pwm_to_angle(self.rc_input_pwm[1], self.max_pitch_deg)
        return roll, pitch

    def _manual_attitude_inputs(self):
        roll, pitch = self._manual_angle_inputs()
        yaw = self._map_pwm_to_rate(self.rc_input_pwm[2], self.max_yaw_rate_deg)
        return roll, pitch, yaw

    def _update_target_altitude(self):
        self._init_altitude_if_needed()
        pwm = self.rc_input_pwm[3]
        if pwm > 1500:
            rate = ((pwm - 1500) / 500.0) * self.max_climb_rate
        elif pwm < 1500:
            rate = ((pwm - 1500) / 500.0) * self.max_descent_rate
        else:
            rate = 0.0
        self.target_altitude += rate * self._dt()

    def _compute_pos_error(self, target, current, lat_ref, yaw_rad):
        dx = (target[0] - current[0]) * 111000.0
        dy = (target[1] - current[1]) * 111000.0 * math.cos(math.radians(lat_ref))
        x_body = math.cos(yaw_rad) * dx + math.sin(yaw_rad) * dy
        y_body = -math.sin(yaw_rad) * dx + math.cos(yaw_rad) * dy
        kp = 2.0
        roll = max(-self.max_roll_deg, min(self.max_roll_deg, kp * y_body))
        pitch = max(-self.max_pitch_deg, min(self.max_pitch_deg, kp * x_body))
        return roll, pitch

    def _init_altitude_if_needed(self):
        now = time.time()
        if self.target_altitude is None:
            self.target_altitude = self.last_state[2]
        if self.prev_time is None:
            self.prev_time = now

    def _dt(self):
        now = time.time()
        if self.prev_time is None:
            self.prev_time = now
        dt = now - self.prev_time
        self.prev_time = now
        return dt

    def _map_pwm_to_angle(self, pwm, max_angle_deg):
        return ((pwm - 1500) / 500.0) * max_angle_deg

    def _map_pwm_to_rate(self, pwm, max_rate_deg):
        return ((pwm - 1500) / 500.0) * max_rate_deg

    def _map_pwm_to_thrust(self, pwm):
        return max(0.0, min(1.0, (pwm - 1000) / 1000.0))

