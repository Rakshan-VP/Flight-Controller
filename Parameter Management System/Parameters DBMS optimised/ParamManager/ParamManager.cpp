#include "ParamManager.h"

// ---------- INIT ----------
void ParamManager::begin() {
    prefs.begin("params", false);
    loadParams();
}

// ---------- LOAD ----------
void ParamManager::loadParams() {
    paramJSON = prefs.getString("params", "[]");

    DynamicJsonDocument doc(2048);
    auto err = deserializeJson(doc, paramJSON);

    if (err || !doc.is<JsonArray>()) {
        Serial.println("WARN: Corrupted JSON, resetting");
        paramJSON = "[]";
        prefs.putString("params", paramJSON);
    }
}

// ---------- SAVE ----------
void ParamManager::saveParams() {
    prefs.putString("params", paramJSON);
}

// ---------- SEND ----------
void ParamManager::sendAll() {
    Serial.print("START");
    Serial.print(paramJSON);
    Serial.print("END");
}

// ---------- VALIDATION ----------
bool ParamManager::validateParams(JsonArray arr) {
    for (JsonObject obj : arr) {
        if (!obj.containsKey("n") || !obj.containsKey("v"))
            return false;

        if (!obj["n"].is<const char*>()) return false;
        if (!obj["v"].is<float>() && !obj["v"].is<int>()) return false;
    }
    return true;
}

// ---------- HANDLE ----------
void ParamManager::handleCmd(String cmd) {
    cmd.trim();
    if (cmd.length() == 0) return;

    // GET
    if (cmd == "GET") {
        sendAll();
        return;
    }

    // SET ALL
    if (cmd.startsWith("SET_ALL|")) {
        String jsonData = cmd.substring(8);

        DynamicJsonDocument doc(2048);
        auto err = deserializeJson(doc, jsonData);

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

    // CLEAR
    if (cmd == "CLEAR") {
        paramJSON = "[]";
        saveParams();
        Serial.println("OK");
        return;
    }
}

// ---------- NON-BLOCKING SERIAL ----------
void ParamManager::update() {
    while (Serial.available()) {
        char c = Serial.read();

        if (c == '\n') {
            handleCmd(inputBuffer);
            inputBuffer = "";
        } else {
            inputBuffer += c;
        }
    }
}

// ---------- GET PARAM ----------
float ParamManager::get(const char* name, float defaultVal) {
    DynamicJsonDocument doc(2048);
    if (deserializeJson(doc, paramJSON)) return defaultVal;

    for (JsonObject obj : doc.as<JsonArray>()) {
        if (strcmp(obj["n"], name) == 0) {
            return obj["v"];
        }
    }
    return defaultVal;
}

// ---------- SET PARAM ----------
void ParamManager::set(const char* name, float value) {
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, paramJSON);

    bool found = false;

    for (JsonObject obj : doc.as<JsonArray>()) {
        if (strcmp(obj["n"], name) == 0) {
            obj["v"] = value;
            found = true;
            break;
        }
    }

    if (!found) {
        JsonObject obj = doc.createNestedObject();
        obj["n"] = name;
        obj["v"] = value;
    }

    serializeJson(doc, paramJSON);
    saveParams();
}