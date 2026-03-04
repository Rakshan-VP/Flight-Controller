# 2-DOF Roll–Pitch Drone Test Setup (4-String Safety Rig)

## Overview
![WhatsApp Image 2026-02-19 at 3 20 25 AM](https://github.com/user-attachments/assets/0b014028-6946-4b00-b832-73c7e54f164d)

I built this setup to test combined roll and pitch control of my drone after completing 1-DOF roll/pitch testing.  

To improve safety, I constrained the drone using four strings attached to the landing legs and fixed them to a rigid frame. This allows limited roll and pitch motion while preventing the drone from flying away.

---

## Mechanical Setup

- I attached four equal-length strings to the bottom of each drone leg.
- The other ends are fixed to a rigid overhead structure.
- The anchor points form a rectangle.
- The drone is centered below the rectangle.
- All strings are slightly tensioned before arming.

This setup:
- Restricts X and Y translation
- Restricts large vertical movement
- Allows limited roll and pitch motion

---

## Testing Procedure

### 1. Pre-check
- Verified all string lengths are equal
- Checked knot strength
- Confirmed drone CG alignment
- Enabled ESC failsafe

### 2. Initial Test
- Slowly increased throttle
- Ensured tension was evenly distributed

### 3. Roll–Pitch Testing
- Applied roll step input
- Applied pitch step input
- Applied combined roll + pitch input
- Observed system response

---

## Observations Focus

During testing, our main is to monitor:

- Overshoot
- Settling time
- Oscillation behavior
- Cross-axis coupling
- Motor output saturation

---

## Common Issues I Checked For

- Uneven tilt → unequal string length
- Continuous oscillation → string elasticity
- Biased angle → CG misalignment

---

## Note

This setup is only for controlled lab testing and PID validation.  
Final tuning still requires free-flight testing.
