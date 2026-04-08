#ifndef PARAM_MANAGER_H
#define PARAM_MANAGER_H

#include <Arduino.h>
#include <Preferences.h>
#include <ArduinoJson.h>

class ParamManager {
public:
    void begin();
    void update();

    // direct access (optional)
    float get(const char* name, float defaultVal = 0);
    void set(const char* name, float value);

private:
    Preferences prefs;
    String paramJSON = "[]";
    String inputBuffer = "";

    void loadParams();
    void saveParams();

    void sendAll();
    void handleCmd(String cmd);
    bool validateParams(JsonArray arr);
};

#endif