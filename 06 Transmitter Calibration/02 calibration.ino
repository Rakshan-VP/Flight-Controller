
#define P1 32  // Yaw
#define P2 33  // Throttle
#define P3 34  // Roll
#define P4 35  // Pitch

#define OK_BTN 12

int minVal[4] = {4095, 4095, 4095, 4095};
int maxVal[4] = {0, 0, 0, 0};

int centerVal[3]; // only for P1, P3, P4

int readSmooth(int pin) {
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(pin);
    delay(2);
  }
  return sum / 10;
}

void waitButton() {
  while (digitalRead(OK_BTN) == HIGH);
  delay(200);
  while (digitalRead(OK_BTN) == LOW);
  delay(200);
}

void setup() {
  Serial.begin(115200);
  pinMode(OK_BTN, INPUT_PULLUP);

  delay(1000);

  // -------- MIN/MAX --------
  Serial.println("STEP 1: Move ALL sticks FULL range");
  Serial.println("Throttle: min ↔ max");
  Serial.println("Press button 1 when done");

  while (digitalRead(OK_BTN) == HIGH) {

    int vals[4] = {
      readSmooth(P1),
      readSmooth(P2),
      readSmooth(P3),
      readSmooth(P4)
    };

    for (int i = 0; i < 4; i++) {
      if (vals[i] < minVal[i]) minVal[i] = vals[i];
      if (vals[i] > maxVal[i]) maxVal[i] = vals[i];
    }
  }

  waitButton();

  Serial.println("Min/Max captured");

  // -------- CENTER (except throttle) --------
  Serial.println("\nSTEP 2: Center Yaw, Roll, Pitch ONLY");
  Serial.println("Leave throttle anywhere");
  Serial.println("Press button");

  waitButton();

  centerVal[0] = readSmooth(P1); // Yaw
  centerVal[1] = readSmooth(P3); // Roll
  centerVal[2] = readSmooth(P4); // Pitch

  // -------- PRINT --------
  Serial.println("\n=== CALIBRATION RESULTS ===");

  Serial.print("Yaw (P1) -> Min: "); Serial.print(minVal[0]);
  Serial.print(" Center: "); Serial.print(centerVal[0]);
  Serial.print(" Max: "); Serial.println(maxVal[0]);

  Serial.print("Throttle (P2) -> Min: "); Serial.print(minVal[1]);
  Serial.print(" Max: "); Serial.println(maxVal[1]);

  Serial.print("Roll (P3) -> Min: "); Serial.print(minVal[2]);
  Serial.print(" Center: "); Serial.print(centerVal[1]);
  Serial.print(" Max: "); Serial.println(maxVal[2]);

  Serial.print("Pitch (P4) -> Min: "); Serial.print(minVal[3]);
  Serial.print(" Center: "); Serial.print(centerVal[2]);
  Serial.print(" Max: "); Serial.println(maxVal[3]);
}

void loop() {}