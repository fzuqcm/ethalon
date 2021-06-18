
/************************** LIBRARIES **************************/
#include <BasicLinearAlgebra.h>
#include <Wire.h>
#include "src/Adafruit_MCP9808.h"
#include <ADC.h>

/*************************** DEFINE ***************************/
// potentiometer AD5252 I2C address is 0x2C(44)
#define ADDRESS 0x2C
// potentiometer AD5252 default value for compatibility with openQCM Q-1 shield @5VDC
#define POT_VALUE 240 //254
// reference clock
#define REFCLK 125000000

/*************************** VARIABLE DECLARATION ***************************/
// current input frequency
long freq = 0;
// DDS Synthesizer AD9851 pin function
int WCLK = A8;
int DATA = A9;
int FQ_UD = A1;
// frequency tuning word
long FTW;
float temp_FTW; // temporary variable
// phase comparator AD8302 pinout
int AD8302_PHASE = 20;
int AD8302_MAG = 37;
//int AD83202_REF = 17;
int AD83202_REF = 34;

// TODO
double val = 0;

// Create the MCP9808 temperature sensor object
Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
// init temperature variable
//float temperature = 0;

// LED pin
int ledPin1 = 24;
int ledPin2 = 25;

// ADC init variabl
boolean WAIT = true;
// ADC waiting delay microseconds
int WAIT_DELAY_US = 300;
// ADC averaging
boolean AVERAGING = true;
// inint number of averaging
int AVERAGE_SAMPLE = 32;
// teensy ADC averaging init
int ADC_RESOLUTION = 13;

// init output ad8302 measurement (cast to double)
double measure_phase = 0;
double measure_mag = 0;

/*************************** FUNCTIONS ***************************/

/* AD9851 set frequency fucntion */
void SetFreq(long frequency)
{
  // set to 125 MHz internal clock
  temp_FTW = (frequency * pow(2, 32)) / REFCLK;
  FTW = long(temp_FTW);

  long pointer = 1;
  int pointer2 = 0b10000000;
  int lastByte = 0b10000000;

  /* 32 bit dds tuning word frequency instructions */
  for (int i = 0; i < 32; i++)
  {
    if ((FTW & pointer) > 0)
      digitalWrite(DATA, HIGH);
    else
      digitalWrite(DATA, LOW);
    digitalWrite(WCLK, HIGH);
    digitalWrite(WCLK, LOW);
    pointer = pointer << 1;
  }

  /* 8 bit dds phase and x6 multiplier refclock*/
  for (int i = 0; i < 8; i++)
  {
    //if ((lastByte & pointer2) > 0) digitalWrite(DATA, HIGH);
    //else digitalWrite(DATA, LOW);
    digitalWrite(DATA, LOW);
    digitalWrite(WCLK, HIGH);
    digitalWrite(WCLK, LOW);
    pointer2 = pointer2 >> 1;
  }

  digitalWrite(FQ_UD, HIGH);
  digitalWrite(FQ_UD, LOW);

  //FTW = 0;
}

/*************************** SETUP ***************************/
void setup()
{
  // Initialise I2C communication as Master
  Wire.begin();
  // Initialise serial communication, set baud rate = 9600
  Serial.begin(115200);

  // set potentiometer value
  // Start I2C transmission
  Wire.beginTransmission(ADDRESS);
  // Send instruction for POT channel-0
  Wire.write(0x01);
  // Input resistance value, 0x80(128)
  Wire.write(POT_VALUE);
  // Stop I2C transmission
  Wire.endTransmission();

  // AD9851 set pin mode
  pinMode(WCLK, OUTPUT);
  pinMode(DATA, OUTPUT);
  pinMode(FQ_UD, OUTPUT);

  // AD9851 enter serial mode
  digitalWrite(WCLK, HIGH);
  digitalWrite(WCLK, LOW);
  digitalWrite(FQ_UD, HIGH);
  digitalWrite(FQ_UD, LOW);

  // AD8302 set pin mode
  pinMode(AD8302_PHASE, INPUT);
  pinMode(AD8302_MAG, INPUT);
  pinMode(AD83202_REF, INPUT);

  // Teensy 3.6 set  adc resolution
  analogReadResolution(ADC_RESOLUTION);

  // begin temperature sensor
  tempsensor.begin();

  // turn on the light
  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);
  digitalWrite(ledPin1, HIGH);
  digitalWrite(ledPin2, HIGH);

  while (!Serial)
  {

    ; // wait for serial port to connect. Needed for native USB port only
  }
}

int legacyRead(String msg)
{
  int d0 = msg.indexOf(';');
  int d1 = msg.indexOf(';', d0 + 1);

  if (d0 == -1 || d1 == -1 || d0 == d1)
  {
    return 1;
  }

  long f0 = msg.substring(0, d0).toInt();
  long f1 = msg.substring(d0 + 1, d1).toInt();
  long f2 = msg.substring(d1 + 1).toInt();

  if (!f0 || !f1 || !f2)
  {
    return 2;
  }

  // 9990000;10010000;40
  double measure_phase = 0;
  double measure_mag = 0;

  for (long f = f0; f <= f1; f += f2)
  {
    SetFreq(f);
    if (WAIT)
      delayMicroseconds(WAIT_DELAY_US);

    int app_phase = 0;
    int app_mag = 0;

    for (int i = 0; i < AVERAGE_SAMPLE; i++)
    {
      app_phase += analogRead(AD8302_PHASE);
      app_mag += analogRead(AD8302_MAG);
    }

    measure_phase = 1.0 * app_phase / AVERAGE_SAMPLE;
    measure_mag = 1.0 * app_mag / AVERAGE_SAMPLE;

    Serial.print(measure_mag);
    Serial.print(";");
    Serial.print(measure_phase);
    Serial.println();
  }

  tempsensor.shutdown_wake(0);
  float temperature = tempsensor.readTempC();

  Serial.print(temperature);
  Serial.print(";");
  Serial.println("s");

  return 0;
}

const int DIRTY_NUM = 64;
const int DIRTY_RANGE = 16384;

long gradient1(long left_freq, long right_freq)
{
  int step_size = (right_freq - left_freq) / DIRTY_NUM;
  if (step_size <= 1)
  {
    return left_freq + (DIRTY_NUM / 2) * step_size;
  }

  int a;
  int max_a = 0;
  int max_f = 0;

  for (long f = left_freq; f <= right_freq; f += step_size)
  {
    SetFreq(f);
    if (WAIT)
      delayMicroseconds(WAIT_DELAY_US);
    a = analogRead(AD8302_MAG);

    if (a > max_a)
    {
      max_a = a;
      max_f = f;
    }
  }

  return gradient1(max_f - 2 * step_size, max_f + 2 * step_size);
}

const int DEFAULT_CALIB_FREQ = 10000000;
const int DEFAULT_RANGE = 65536;
const int SWEEP_STEP = 32;
const int SWEEP_RANGE = 3072;
const int SWEEP_COUNT = SWEEP_RANGE / SWEEP_STEP + 1;
const int SWEEP_REPEAT = 16;

long calib_freq = DEFAULT_CALIB_FREQ;

double sweepFrequency(long rf)
{
  String str = String();
  BLA::Matrix<SWEEP_COUNT, 3> A;
  BLA::Matrix<SWEEP_COUNT> b;

  long f = rf - (SWEEP_RANGE / 2);
  double cumsum = 0;

  SetFreq(f);
  delayMicroseconds(WAIT_DELAY_US * 3);
  analogRead(AD8302_MAG);

  for (int i = 0; i < SWEEP_COUNT; i++, f += SWEEP_STEP)
  {
    SetFreq(f);
    if (WAIT)
      delayMicroseconds(WAIT_DELAY_US);
    cumsum = 0;

    for (int j = 0; j < SWEEP_REPEAT; j++)
    {
      cumsum += analogRead(AD8302_MAG);
    }

    b(i) = cumsum / (double)SWEEP_REPEAT;
    A(i, 0) = i * i;
    A(i, 1) = i;
    A(i, 2) = 1;

    if (b(i) < 4000)
    {
      return -1;
    }

    str.concat(b(i)).concat(';');
  }

  //  Serial.println(str);

  BLA::Matrix<3> coeffs = ((~A) * A).Inverse() * (~A) * b;
  double result = -coeffs(1) / (2 * coeffs(0)) * (double)SWEEP_STEP + (double)rf;

  //  Serial.println(result);

  calib_freq = (long)result;

  return result;
}

int modernRead(String msg)
{
  long param = msg.substring(2).toInt();
  char cmd = msg.charAt(0);
  long f;
  double rf;
  float t;

  switch (cmd)
  {
  case 'c':
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency(f);
    Serial.println(rf);
    tempsensor.shutdown_wake(0);
    t = tempsensor.readTempC();
    Serial.println(t);
    break;
  case 'm':
    f = gradient1(calib_freq - DIRTY_RANGE, calib_freq + DIRTY_RANGE);
    rf = sweepFrequency(f);
    Serial.println(rf);
    tempsensor.shutdown_wake(0);
    t = tempsensor.readTempC();
    Serial.println(t);
    break;
  case 'p':
    break;
  default:
    return 1;
  }

  return 0;
}

int message = 0;
boolean debug = true;
long pre_time = 0;
long last_time = 0;

int byteAtPort = 0;

/*************************** LOOP ***************************/
void loop()
{
  if (!(Serial.available() > 0))
  {
    return;
  }

  String msg = Serial.readStringUntil('\n');
  bool useModern = msg.indexOf(';') == -1;

  int retVal;
  if (useModern)
  {
    retVal = modernRead(msg);
  }
  else
  {
    retVal = legacyRead(msg);
  }

  Serial.println("Modern: " + String(useModern));
  Serial.println("RetVal: " + String(retVal));
}
