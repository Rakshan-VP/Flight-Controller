# Trajectory-Based Altitude Control
![tracking](https://github.com/user-attachments/assets/4fc034ef-b821-4e18-9ed9-c552b60ae252)

This module implements a **velocity-driven altitude trajectory controller** that tracks a desired altitude path by commanding *rise* and *descent* velocities instead of setting altitude steps directly.  
The controller adjusts altitude smoothly toward a target and **holds automatically** once the target is reached.

Traditional altitude control often requires **gain scheduling** because controller dynamics change significantly at different altitude setpoints. In contrast, this trajectory-based approach makes the altitude setpoint evolve *continuously at a controlled rate*, which ensures that:

- A **single set of gains** works reliably across the entire altitude envelope.
- The controller sees a **smooth reference trajectory** rather than abrupt steps.
- Tracking performance becomes predictable and easier to tune.
- Overshoot and oscillations are inherently reduced.

---

## How It Works

1. The system compares current altitude command (`h1`) with the desired target altitude (`h2`).
2. If `h2 > h1`, the controller commands a **rise velocity**.
3. If `h2 < h1`, it commands a **descent velocity**.
4. The altitude command is integrated over time using the simulation/clock time.
5. Once the altitude error becomes small, the controller **holds** the altitude.
6. A discrete PID loop closes the control to follow this trajectory very closely.

Because the reference trajectory itself is smooth, the PID gains do not have to be retuned for each altitude range.  
This design removes the need for per-altitude gain scheduling.

---

## Benefits

- **Single PID gain set** for all altitudes  
- **High-fidelity trajectory tracking** using velocity-based shaping  
- **Reduced derivative spikes** due to smooth setpoint evolution  
- **Improved stability** compared to step-input altitude commands  
- **Cleaner control loop** with predictable dynamics  
- **Better simulator realism** for UAV and robotics applications

---

## Altitude Tracking Performance
<img width="1832" height="1170" alt="Tracking" src="https://github.com/user-attachments/assets/7274c389-5e7c-4518-81e7-3ccb2bce58bb" />

The plot above (altitude vs. time) demonstrates how the system tracks the desired trajectory extremely closely.  
Even with rapid target changes, the controller:

- rises and descends smoothly,  
- follows the generated trajectory with minimal error, and  
- converges to the target altitude without overshoot.

This validates that the trajectory-based controller provides **tight tracking** without requiring altitude-dependent tuning.

---

## Usage Overview

1. Provide a target altitude in the gui with hold time and tolerance.  
2. The trajectory generator converts the target into a continuous altitude command using rise and descent velocities.  
3. The PID block tracks this trajectory.  
4. The controller holds stable at the final altitude until a new target is given.

---

## Key Idea

**Instead of controlling altitude directly, we control a trajectory.**  
This approach produces smooth altitude transitions while allowing a single, fixed tuning to work over the entire operating range.

---

