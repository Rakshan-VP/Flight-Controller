#include <Servo.h>

// 6 Servo objects
Servo servo1, servo2, servo3, servo4, servo5, servo6;

void setup() {
  servo1.attach(PB13);
  servo2.attach(PB14);
  servo3.attach(PB15);
  servo4.attach(PA8);
  servo5.attach(PA9);
  servo6.attach(PA10);

  Serial.begin(115200);
  Serial.println("Servo Test Started");
}

void loop() {
  for (int angle = 0; angle <= 180; angle += 10) {
    setAllServos(angle);
    delay(200);
  }

  for (int angle = 180; angle >= 0; angle -= 10) {
    setAllServos(angle);
    delay(200);
  }
}

void setAllServos(int angle) {
  servo1.write(angle);
  servo2.write(angle);
  servo3.write(angle);
  servo4.write(angle);
  servo5.write(angle);
  servo6.write(angle);

  Serial.print("Angle: ");
  Serial.println(angle);
}
