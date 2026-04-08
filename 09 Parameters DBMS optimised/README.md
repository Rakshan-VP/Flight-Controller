# 🚀 Parameter DBMS — ESP32 + PyQt GUI

A minimal system to **store, edit, and sync parameters** between an ESP32 and a desktop GUI.

---

## 📑 Table of Contents

- [Communication Protocol](#-communication-protocol)
- [How to Use (End-to-End)](#-how-to-use-end-to-end)
- [JSON Storage & Merge Logic](#-json-storage--merge-logic)
- [ParamManager Library](#-parammanager-library)
- [Notes & Limitations](#-notes--limitations)

---

## 🔌 Communication Protocol

Communication happens over **Serial at 115200 baud** using a simple text-based protocol.


### 📥 `GET` — Read All Parameters

**GUI sends:**
```
GET
```

**ESP32 responds:**
```
START[{"n":"P1","v":10},{"n":"P2","v":20}]END
```

| Token | Purpose |
|-------|---------|
| `START` / `END` | Framing markers for complete data detection |
| Payload | JSON array of `{ name, value }` objects |

---

### 📤 `SET_ALL` — Write All Parameters

**GUI sends:**
```
SET_ALL|[{"n":"P1","v":15},{"n":"P2","v":25}]
```

**ESP32:**
1. Validates JSON
2. Stores to NVS
3. Responds:

```
OK
```

---

### 🧹 `CLEAR` — Reset All Parameters

```
CLEAR
```

---

### ⚙️ Key Design Points

| Feature | Description |
|--------|-------------|
| **Chunked write (GUI)** | Avoids UART overflow on large payloads |
| **Framed read (`START...END`)** | Ensures complete data before parsing |
| **ACK (`OK`)** | Confirms successful write to NVS |
| **Non-blocking parser (ESP32)** | Handled in `update()` — never blocks `loop()` |

---

## ▶️ How to Use (End-to-End)

### Step 1 — Flash ESP32

Include `ParamManager` in your `.ino` and initialize it:

```cpp
params.begin();
```

### Step 2 — Run GUI

```bash
python PARAM_DBMS_GUI.py
```

### Step 3 — Workflow

```
Select COM port → Connect
       ↓
GUI sends GET → loads parameters into table
       ↓
Edit values / groups / descriptions
       ↓
Click WRITE
       ↓
GUI sends SET_ALL → ESP32 replies OK
```

### 💾 What Gets Saved Where

| Location | Data Stored |
|----------|------------|
| **ESP32 (NVS)** | `name` + `value` |
| **PC (`params_db.json`)** | `group` + `default` + `description` |

---

## 📦 JSON Storage & Merge Logic

### ESP32 Storage (NVS)

Stored as a JSON string using `Preferences`:

```json
[
  {"n": "ROLL_P", "v": 1.2},
  {"n": "YAW_D",  "v": 0.02}
]
```

> The entire array is **overwritten** on every `SET_ALL`.

---

### GUI Local DB (`params_db.json`)

Stores metadata for each parameter:

```json
[
  {"g": "PID", "n": "ROLL_P", "d": 1.0, "desc": "Roll proportional gain"}
]
```

---

### 🔀 Merge Logic

When the GUI loads, it merges **ESP32 data + Local DB** into the table by matching on `name`:

```
ESP32 response  →  { n, v }
Local DB        →  { g, n, d, desc }
                         ↓
              Matched by name (n)
                         ↓
              Merged row in table
```

| Field | Source |
|-------|--------|
| `name` | ESP32 |
| `value` | ESP32 |
| `group` | Local DB |
| `default` | Local DB |
| `description` | Local DB |

> **If a parameter is not found in the local DB:**
> - Group → *(empty)*
> - Default → `0`
> - Description → *(empty)*

---

## 📚 ParamManager Library

### Setup

```cpp
#include "ParamManager.h"
ParamManager params;
```

### Initialize

```cpp
void setup() {
    Serial.begin(115200);
    params.begin();
}
```

### Required Loop Hook

```cpp
void loop() {
    params.update();  // Handles all serial commands — never skip this
}
```

### Get a Parameter

```cpp
float val = params.get("ROLL_P", 1.0);
// Returns stored value, or the default if the key is missing
```

### Set a Parameter (Optional)

```cpp
params.set("ROLL_P", 1.5);
// Updates the in-memory JSON and saves to NVS immediately
```

---

### ✅ Minimal Working Example

```cpp
#include "ParamManager.h"
ParamManager params;

void setup() {
    Serial.begin(115200);
    params.begin();
}

void loop() {
    params.update();

    float kp = params.get("ROLL_P", 1.0);
    // Use kp in your control loop
}
```

---

## ⚠️ Notes & Limitations

| Constraint | Detail |
|-----------|--------|
| **JSON buffer** | ~2 KB — keep total parameter count reasonable |
| **`params.update()`** | Must be called every loop iteration |
| **Baud rate** | ESP32 and GUI must both use `115200` |
