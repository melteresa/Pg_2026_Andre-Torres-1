#include <AccelStepper.h>

const int PIN_AIN1 = 2;
const int PIN_AIN2 = 4;
const int PIN_PWMA = 3;
const int PIN_BIN1 = 7;
const int PIN_BIN2 = 8;
const int PIN_PWMB = 5;
const int PIN_STEP = 9;
const int PIN_DIR = 10;

AccelStepper stepper(AccelStepper::DRIVER, PIN_STEP, PIN_DIR);

unsigned long lastSerialMs = 0;
const unsigned long COMMAND_TIMEOUT = 500;

int webCarro = 0;
int webElev = 0;
int webGiro = 0;

const int JOY_DEADZONE = 60;
const int MAX_PWM = 255;
const int STEP_SPEED = 500;
const int STEP_ACCEL = 300;

void setup() {
  pinMode(PIN_AIN1, OUTPUT);
  pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_PWMA, OUTPUT);
  pinMode(PIN_BIN1, OUTPUT);
  pinMode(PIN_BIN2, OUTPUT);
  pinMode(PIN_PWMB, OUTPUT);

  Serial.begin(9600);
  stepper.setMaxSpeed(STEP_SPEED);
  stepper.setAcceleration(STEP_ACCEL);
}

int readJoystickAxis(int pin) {
  int value = analogRead(pin) - 512;
  if (abs(value) < JOY_DEADZONE) {
    return 0;
  }
  return map(value, -512, 512, -MAX_PWM, MAX_PWM);
}

void driveMotor(int pin1, int pin2, int pwmPin, int speed) {
  if (speed == 0) {
    digitalWrite(pin1, LOW);
    digitalWrite(pin2, LOW);
    analogWrite(pwmPin, 0);
    return;
  }

  if (speed > 0) {
    digitalWrite(pin1, HIGH);
    digitalWrite(pin2, LOW);
    analogWrite(pwmPin, speed);
  } else {
    digitalWrite(pin1, LOW);
    digitalWrite(pin2, HIGH);
    analogWrite(pwmPin, -speed);
  }
}

void stopAll() {
  webCarro = 0;
  webElev = 0;
  webGiro = 0;
}

void applySerialCommand(char command) {
  switch (command) {
    case 'F':
      webCarro = 200;
      break;
    case 'B':
      webCarro = -200;
      break;
    case 'U':
      webElev = 200;
      break;
    case 'D':
      webElev = -200;
      break;
    case 'L':
      webGiro = -300;
      break;
    case 'R':
      webGiro = 300;
      break;
    case 'S':
      stopAll();
      break;
    default:
      break;
  }
}

void readSerialCommands() {
  while (Serial.available()) {
    char incoming = Serial.read();
    if (incoming >= 'a' && incoming <= 'z') {
      incoming = incoming - 'a' + 'A';
    }

    applySerialCommand(incoming);
    lastSerialMs = millis();
  }
}

void checkTimeout() {
  if (millis() - lastSerialMs > COMMAND_TIMEOUT) {
    webCarro = 0;
    webElev = 0;
    webGiro = 0;
  }
}

void loop() {
  readSerialCommands();
  checkTimeout();

  int joystickCarro = readJoystickAxis(A0);
  int joystickElev = readJoystickAxis(A1);
  int joystickGiro = readJoystickAxis(A2);

  int commandedCarro = constrain(joystickCarro + webCarro, -MAX_PWM, MAX_PWM);
  int commandedElev = constrain(joystickElev + webElev, -MAX_PWM, MAX_PWM);
  int commandedGiro = constrain(joystickGiro + webGiro, -STEP_SPEED, STEP_SPEED);

  driveMotor(PIN_AIN1, PIN_AIN2, PIN_PWMA, commandedCarro);
  driveMotor(PIN_BIN1, PIN_BIN2, PIN_PWMB, commandedElev);

  stepper.setSpeed(commandedGiro);
  stepper.runSpeed();

  delay(20);
}