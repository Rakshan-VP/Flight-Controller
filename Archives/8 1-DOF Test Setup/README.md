# 1 DOF Test Setup

This repository contains code and test setups for a **1 Degree of Freedom (DOF) Test Rig**.  
It is organized into three main subfolders for different stages of testing.

---

## 📂 Folder Structure

### 1. **Level testing**
- **gui.py** – Python GUI for sending/receiving data between the flight controller and ground control station.  
- **fc.ino** – Flight controller code for processing inputs and stabilization.  
- **gcs.ino** – Ground Control Station (GCS) code for communication and monitoring.

### 2. **Testing motors**
- Arduino/STM32 code to test each motor individually using ESCs.  
- Used to calibrate ESCs and verify motor functionality.

### 3. **Roll pitch pid testing in 1 dof test rig**
- **gui.py** – Interface to visualize roll/pitch responses.  
- **fc.ino** – Flight controller code with PID control for 1 DOF stabilization.  
- **gcs.ino** – Ground station code to monitor real-time PID performance.  
- Focused on PID tuning and validation using the test rig.

---

## 🛠 Test Setup Diagram
A schematic/diagram of the **1 DOF Test Rig** will be added here.  

---

## 🚀 Purpose
- Validate motor functionality.  
- Test communication between FC and GCS.  
- Tune and evaluate PID control for roll/pitch stabilization in a 1 DOF environment.  
