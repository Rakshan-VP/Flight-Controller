#include <Preferences.h>
#include <ArduinoJson.h>

Preferences prefs;

String paramJSON = "[]";

// ---------- LOAD ----------
void loadParams() {
    paramJSON = prefs.getString("params", "[]");

    DynamicJsonDocument doc(2048);
    DeserializationError err = deserializeJson(doc, paramJSON);

    if (err || !doc.is<JsonArray>()) {
        Serial.println("WARN: Corrupted JSON, resetting");
        paramJSON = "[]";
        prefs.putString("params", paramJSON);
    }
}

// ---------- SAVE ----------
void saveParams() {
    prefs.putString("params", paramJSON);
}

// ---------- SEND ----------
void sendAll() {
    Serial.print("START");
    Serial.print(paramJSON);
    Serial.print("END");
}

// ---------- VALIDATION (ONLY n + v) ----------
bool validateParams(JsonArray arr) {
    for (JsonObject obj : arr) {

        if (!obj.containsKey("n") || !obj.containsKey("v")) {
            return false;
        }

        if (!obj["n"].is<const char*>()) return false;
        if (!obj["v"].is<float>() && !obj["v"].is<int>()) return false;
    }
    return true;
}

// ---------- HANDLE ----------
void handleCmd(String cmd) {
    cmd.trim();

    if (cmd.length() == 0) return;

    // ---------- GET ----------
    if (cmd == "GET") {
        sendAll();
        return;
    }

    // ---------- SET ALL ----------
    if (cmd.startsWith("SET_ALL|")) {
        String jsonData = cmd.substring(8);

        DynamicJsonDocument doc(2048);
        DeserializationError err = deserializeJson(doc, jsonData);

        if (err) {
            Serial.println("ERR_JSON");
            return;
        }

        if (!doc.is<JsonArray>()) {
            Serial.println("ERR_FORMAT");
            return;
        }

        JsonArray arr = doc.as<JsonArray>();

        if (!validateParams(arr)) {
            Serial.println("ERR_VALIDATION");
            return;
        }

        paramJSON = jsonData;
        saveParams();

        Serial.println("OK");
        return;
    }

    // ---------- CLEAR ----------
    if (cmd == "CLEAR") {
        paramJSON = "[]";
        saveParams();
        Serial.println("OK");
        return;
    }
}

// ---------- SETUP ----------
void setup() {
    Serial.begin(115200);

    prefs.begin("params", false);

    loadParams();

    Serial.println("READY");
}

// ---------- LOOP ----------
void loop() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        handleCmd(cmd);
    }
}