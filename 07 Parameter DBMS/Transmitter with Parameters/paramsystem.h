#ifndef PARAM_SYSTEM_H
#define PARAM_SYSTEM_H

#include <Arduino.h>
#include <Preferences.h>
#include <ArduinoJson.h>

// Global Variables
static Preferences _param_prefs;
static String _paramJSON = "[]";
static bool _param_updated = false;
static StaticJsonDocument<2048> _param_doc;

// Forward declaration of internal helper
void _param_save() {
    _param_prefs.putString("params", _paramJSON);
}

// Send all parameters via Serial
void param_sendAll() {
    Serial.println("START");
    Serial.println(_paramJSON);
    Serial.println("END");
}

// Validate JSON structure
bool param_validate(JsonArray arr) {
    for (JsonObject obj : arr) {
        if (!obj.containsKey("n") || !obj.containsKey("v") || 
            !obj.containsKey("u") || !obj.containsKey("min") || 
            !obj.containsKey("max")) {
            return false;
        }
        float v = obj["v"];
        float mn = obj["min"];
        float mx = obj["max"];
        if (mn > mx || v < mn || v > mx) return false;
    }
    return true;
}

// Initialize System
void param_init() {
    _param_prefs.begin("params", false);
    _paramJSON = _param_prefs.getString("params", "[]");

    if (deserializeJson(_param_doc, _paramJSON) || !_param_doc.is<JsonArray>()) {
        _paramJSON = "[]";
        _param_prefs.putString("params", _paramJSON);
        deserializeJson(_param_doc, _paramJSON);
    }
}

// Call this in loop() to handle Serial commands
void param_handle() {
    static String buffer = "";
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            String cmd = buffer;
            buffer = "";
            cmd.trim();

            if (cmd == "GET") {
                param_sendAll();
            } 
            else if (cmd.startsWith("SET_ALL|")) {
                String json = cmd.substring(8);
                StaticJsonDocument<2048> temp;
                if (!deserializeJson(temp, json) && temp.is<JsonArray>() && param_validate(temp.as<JsonArray>())) {
                    _paramJSON = json;
                    _param_save();
                    deserializeJson(_param_doc, _paramJSON); // Update cache
                    Serial.println("OK");
                    _param_updated = true;
                } else {
                    Serial.println("ERR_INVALID");
                }
            } 
            else if (cmd == "CLEAR") {
                _paramJSON = "[]";
                _param_save();
                deserializeJson(_param_doc, _paramJSON);
                Serial.println("OK");
                _param_updated = true;
            }
        } else {
            buffer += c;
        }
    }
}

// Get a value by name
float param_get(const char* name, float def = 0) {
    for (JsonObject obj : _param_doc.as<JsonArray>()) {
        if (strcmp(obj["n"], name) == 0) {
            return obj["v"];
        }
    }
    return def;
}

// Check if parameters changed via Serial
bool param_isUpdated() {
    if (_param_updated) {
        _param_updated = false;
        return true;
    }
    return false;
}

#endif