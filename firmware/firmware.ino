
/***********************************************************
 * FZU: This is a FZU version of QCM firmware. Some parts are not changed from the Italien one,
 * because it is only setting up the digital inputs and outputs.
 * From version 3.10 support FZU HW v. 5.0
 ***********************************************************/

/******************************* LIBRARIES *****************************/
/** FZU: YOU NEED TO INSTALL BasicLinearAlgebra LIBRARY FROM THE MENU **/
#include <ArduinoJson.h>
#include <BasicLinearAlgebra.h>
#include <Wire.h>
#include "src/Adafruit_MCP9808.h"
#include <ADC.h>
#include "Arduino.h"
#include <TeensyID.h>
#include <limits>
#include <vector>    // Pro použití std::vector
#include <algorithm> // Pro použití std::sort
#include <numeric>   // Pro použití std::accumulate
#include <SPI.h>
// #include "MedianFilterLib2.h"

/*************************** DEFINE ***************************/
#define FW_AUTHOR "FZU Team"
#define FW_NAME "FZU QCM Firmware"
#define FW_VERSION "3.12.0"
#define FW_DATE "19.8.2024"
#define FW_HINT "Legacy read Am/Ph normalization"

#define TEENSY "Teensy 3.6"

// reference clock
#define REFCLK 125000000
unsigned long refclk = REFCLK; // Italy is default
int lastByte = 0b00000000;

char SN[8] = "0000000";
char HW[13] = "None        ";

unsigned long sf = 10000000; // default frequency

/*************************** VARIABLE DECLARATION ***************************/
// potentiometer AD5252 default value for compatibility with openQCM Q-1 shield @5VDC
int POT_VALUE = 240; // 254
String potval_str = String(POT_VALUE);
// current input frequency
long freq = 0;
// DDS Synthesizer AD9851 pin function for Italy HW
int WCLK = A8;
int DATA = A9;
int FQ_UD = A1;
// frequency tuning word
unsigned long FTW;
float temp_FTW; // temporary variable
// phase comparator AD8302 pinout
int AD8302_PHASE = 20;
int AD8302_MAG = 37;
// int AD83202_REF = 17;
int AD83202_REF = 34;

// TODO
double val = 0;

// Create the MCP9808 temperature sensor object
Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
// init temperature variable
// float temperature = 0;

// LED pin
int LED1 = 24;
// int LED2 = 25;
// int LED3 = 26;

// Potentiometer address
int POT_ADDRESS = 0x2C;  // Italy is default

//ADS8353
const int csPin = 10;     // Chip Select pin
// const int sdoAPin = 12;   // SDO_A pin na Teensy 3.6 (MISO)
// const int sdoBPin = 9;    // SDO_B pin na Teensy 3.6 (jiný volný digitální pin)
// const int sdiPin = 11;    // SDI pin na Teensy 3.6 (MOSI)
const float referenceVoltage = 3.3; // 5.0

// ADC init variabl
boolean WAIT = true;
boolean WAIT_LONG = false;
// ADC waiting delay microseconds
// int WAIT_DELAY_US = 300;
// int WAIT_DELAY_US = 100;
// int AVERAGE_COUNT = 50;

int WAIT_DELAY_US = 100;
int AVERAGE_COUNT = 32;
int DISCARD_COUNT = 8;
int ITALY_CONSTANT = 1;
int Italy = 1;

// ADC averaging
boolean AVERAGING = true;
// inint number of averaging
int AVERAGE_SAMPLE = 32;
// teensy ADC averaging init
int ADC_RESOLUTION = 13;

// init output ad8302 measurement (cast to double)
double measure_phase = 0;
double measure_mag = 0;

const int DEFAULT_CALIB_FREQ = 10000000;
const int DEFAULT_RANGE = 65536;

const int SWEEP_STEP = 32;
const int SWEEP_RANGE = 1280;
const int SWEEP_COUNT = SWEEP_RANGE / SWEEP_STEP + 1;
const int SWEEP_REPEAT = 16;

const int DIS_STEP = 256;
const int DIS_RANGE = 16384;
const int DIS_COUNT = DIS_RANGE / DIS_STEP + 1;

BLA::Matrix<3, SWEEP_COUNT> A_dagger;
BLA::Matrix<SWEEP_COUNT, 3> A;

const int POLY_DEGREE = 5;
BLA::Matrix<POLY_DEGREE, SWEEP_COUNT> B_dagger;
BLA::Matrix<SWEEP_COUNT, POLY_DEGREE> B;
double quad_res;
double res;

StaticJsonDocument<256> fw;
StaticJsonDocument<4096> data;
JsonArray magValues = data.createNestedArray("magnitude");
JsonArray phaseValues = data.createNestedArray("phase");
uint64_t dseq = 0;

/*************************** SETUP ***************************/
void setup()
{
  // Initialise serial communication, set baud rate = 9600
  Serial.begin(115200);
  while (!Serial) {
    ; // Čeká, dokud není inicializován sériový port (platí pro desky s nativním USB)
  }

  // Initialise I2C communication as Master
  Wire.begin();

  // Check HW vendor
  Wire.beginTransmission(0x2C);
  if (Wire.endTransmission() == 0)
  {
    // Serial.println("Italy");
    sprintf(HW, "Italy 125MHz");
  }
  else
  {
    // Serial.println("FZU v.5");
    sprintf(HW, "FZU 6 20MHz ");
    POT_ADDRESS = 0x00;
    WCLK = A7;
    DATA = A8;
    refclk = 30000000 * 6;
    lastByte = 0b10000000;
    LED1 = 39;
    ITALY_CONSTANT = 4;
    Italy = 0;

    pinMode(csPin, OUTPUT);
    digitalWrite(csPin, HIGH); // Neaktivní stav CS
    // pinMode(sdoAPin, INPUT);
    // pinMode(sdoBPin, INPUT);
    // pinMode(sdiPin, OUTPUT);
    SPI.begin();
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE1)); // Nastavení SPI
    writeCFR(0x8400);  // Nastavení režimu 32-CLK Single-SDO Mode (CFR.B11 = 0, CFR.B10 = 1)
  }

  // set potentiometer value
  if (POT_ADDRESS) {
    // Start I2C transmission
    Wire.beginTransmission(POT_ADDRESS);
    // Send instruction for POT channel-0
    Wire.write(0x01);
    // Input resistance value, 0x80(128)
    Wire.write(POT_VALUE);
    // Stop I2C transmission
    Wire.endTransmission();
  }

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
  pinMode(LED1, OUTPUT);
  // pinMode(LED2, OUTPUT);
  // pinMode(LED3, OUTPUT);
  digitalWrite(LED1, HIGH);
  // digitalWrite(LED2, HIGH);
  // digitalWrite(LED3, HIGH);
  delay(500);
  digitalWrite(LED1, LOW);
  // digitalWrite(LED2, LOW);
  // digitalWrite(LED3, LOW);
 
  for (int i = 0; i < SWEEP_COUNT; i++)
  {
    A(i, 0) = i * i;
    A(i, 1) = i;
    A(i, 2) = 1;
  }

 A_dagger = ((~A) * A).Inverse() * (~A);

  float x;

  for (int i = 0; i < SWEEP_COUNT; i++)
  {
    x = i/SWEEP_COUNT;
    B(i, 0) = 1;
    B(i, 1) = x;
    B(i, 2) = x*x;
    B(i, 3) = x*x*x;
    B(i, 4) = x*x*x*x;
    B(i, 5) = x*x*x*x*x;
  }

  B_dagger = ((~B) * B).Inverse() * (~B);

  fw["name"] = FW_NAME;
  fw["version"] = FW_VERSION;
  fw["date"] = FW_DATE;
  fw["author"] = FW_AUTHOR;
  fw["hint"] = FW_HINT;
  fw["hw"] = HW;
  fw["teensy"] = "Teensy 3.6";
  sprintf(SN, "%u", (unsigned int)teensyUsbSN());
  fw["sn"] = SN;

  while (!Serial)
  {

    ; // wait for serial port to connect. Needed for native USB port only
  }
}

/*************************** ADS8353 SUPPORT ***************************/

void writeCFR(uint16_t config) {
  digitalWrite(csPin, LOW);
  // Odeslání příkazu pro zápis do CFR
  SPI.transfer16(0x8000 | config);  // 0x8000 značí zápis do CFR
  //Zajištění 48 hodinových cyklů pro Frame F1
  for (int i = 0; i < 2; i++) {
    SPI.transfer16(0x0000);  // Dodatkových 32 hodinových cyklů (celkem 48 hodinových cyklů)
  }
  digitalWrite(csPin, HIGH);
}

uint64_t readCFR() {
  uint64_t result = 0;
  // Odeslání prázdného rámce (48 CLK) pro Frame F
  digitalWrite(csPin, LOW);
  for (int i = 0; i < 3; i++) {
    SPI.transfer16(0x0000);  // Celkem 48 hodinových cyklů
  }
  digitalWrite(csPin, HIGH);

  delayMicroseconds(1);

  // Odeslání kontrolního příkazu pro čtení CFR během Frame F1 (48 CLK)
  digitalWrite(csPin, LOW);
  SPI.transfer16(0x3000);  // 0x3000 značí čtení CFR
  for (int i = 0; i < 2; i++) {
    SPI.transfer16(0x0000);  // Dodatkových 32 hodinových cyklů (celkem 48 hodinových cyklů)
  }
  digitalWrite(csPin, HIGH);

  delayMicroseconds(1);

  // Čtení 48 bitů dat během Frame F2 (16 bitů pro CFR a 32 bitů padding)
  digitalWrite(csPin, LOW);
  result = SPI.transfer16(0x0000); // Přečtení prvních 16 bitů 
  result = (result << 16) | SPI.transfer16(0x0000); // Přečtení dalších 16 bitů 
  result = (result << 32) | SPI.transfer16(0x0000); // Přečtení dalších 16 bitů 
  digitalWrite(csPin, HIGH);

  return result;
}

uint64_t readADC() {
  uint64_t result = 0;

  digitalWrite(csPin, LOW); // Aktivace převodníku

  // Čtení 32-bitových dat (16 bitů z kanálu A, 16 bitů z kanálu B)
  result = SPI.transfer16(0x0000); // Přečtení prvních 16 bitů
  result = (result << 16) | SPI.transfer16(0x0000); // Přečtení dalších 16 bitů
  result = (result << 32) | SPI.transfer16(0x0000); // Přečtení dalších 16 bitů

  digitalWrite(csPin, HIGH); // Deaktivace převodníku

  return result;
}

/*************************** SET FREQUENCY ***************************/

/* AD9851 set frequency fucntion */
void SetFreq(unsigned long frequency)
{
  // set internal clock
  temp_FTW = (frequency * pow(2, 32)) / refclk;
  FTW = (unsigned long)temp_FTW;

  long pointer = 1;
  int pointer2 = 0b10000000;

#define DELAY 1
  /* 32 bit dds tuning word frequency instructions */
  for (int i = 0; i < 32; i++)
  {
    if ((FTW & pointer) > 0)
      digitalWrite(DATA, HIGH);
    else
      digitalWrite(DATA, LOW);
    delayMicroseconds(DELAY);
    digitalWrite(WCLK, HIGH);
    delayMicroseconds(DELAY);
    digitalWrite(WCLK, LOW);
    delayMicroseconds(DELAY);
    pointer = pointer << 1;
  }

  /* 8 bit dds phase and x6 multiplier refclock*/
  for (int i = 0; i < 8; i++)
  {
    if ((lastByte & pointer2) > 0)
      digitalWrite(DATA, HIGH);
    else
      digitalWrite(DATA, LOW);
    delayMicroseconds(DELAY);
    digitalWrite(WCLK, HIGH);
    delayMicroseconds(DELAY);
    digitalWrite(WCLK, LOW);
    delayMicroseconds(DELAY);
    pointer2 = pointer2 >> 1;
  }

  digitalWrite(FQ_UD, HIGH);
  delayMicroseconds(DELAY);
  digitalWrite(FQ_UD, LOW);
  delayMicroseconds(DELAY);
}

/*************************** OTHER FUNCTIONS ***************************/

/**
 * FZU: original Italien code, but optimized for better reading
 */
void legacyAmPh(void) {
  if (WAIT) delayMicroseconds(WAIT_DELAY_US);
  if (WAIT_LONG) delay(10);

  double measure_phase = 0;
  double measure_mag = 0;
  uint64_t adcData = 0;
  uint64_t app_phase = 0;
  uint64_t app_mag = 0;

  for (int i = 0; i < AVERAGE_SAMPLE; i++)
  {
    if (Italy) {
      app_phase += analogRead(AD8302_PHASE);
      app_mag += analogRead(AD8302_MAG);
    }
    else {
      adcData = readADC();
      app_phase += adcData & 0xFFFF;
      app_mag += (adcData >> 32) & 0xFFFF;
    }
  }

  measure_phase = 1.0 * app_phase / AVERAGE_SAMPLE;
  measure_mag = 1.0 * app_mag / AVERAGE_SAMPLE;

  Serial.print(measure_mag);
  Serial.print(";");
  Serial.print(measure_phase);
  Serial.println();
}

// int legacyRead(String msg)
// {
//   int d0 = msg.indexOf(';');
//   int d1 = msg.indexOf(';', d0 + 1);

//   if (d0 == -1 || d1 == -1 || d0 == d1)
//   {
//     return 1;
//   }

//   long f0 = msg.substring(0, d0).toInt();
//   long f1 = msg.substring(d0 + 1, d1).toInt();
//   long f2 = msg.substring(d1 + 1).toInt();

//   if (!f0 || !f1 || !f2)
//   {
//     return 2;
//   }

//   // 9990000;10010000;40

//   for (unsigned long f = f0; f <= f1; f += f2)
//   {
//     SetFreq(f);
//     legacyAmPh();
//   }

//   tempsensor.shutdown_wake(0);
//   float temperature = tempsensor.readTempC();

//   Serial.print(temperature);
//   Serial.print(";");
//   Serial.print(POT_VALUE);
//   Serial.print(";");
//   Serial.println("s");

//   return 0;
// }

void legacyAmPh2(double &measure_mag, double &measure_phase) {
  if (WAIT) delayMicroseconds(WAIT_DELAY_US);
  if (WAIT_LONG) delay(10);

  uint64_t adcData = 0;
  uint64_t app_phase = 0;
  uint64_t app_mag = 0;

  for (int i = 0; i < AVERAGE_SAMPLE; i++)
  {
    if (Italy) {
      app_phase += analogRead(AD8302_PHASE);
      app_mag += analogRead(AD8302_MAG);
    }
    else {
      adcData = readADC();
      app_phase += adcData & 0xFFFF;
      app_mag += (adcData >> 32) & 0xFFFF;
    }
  }

  measure_phase = 1.0 * app_phase / AVERAGE_SAMPLE;
  measure_mag = 1.0 * app_mag / AVERAGE_SAMPLE;
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

  double max_amplitude = 0;
  double max_phase = 0;
  double measure_mag = 0;
  double measure_phase = 0;

  int num_samples = (f1 - f0) / f2 + 1;
  double* magnitudes = new double[num_samples];
  double* phases = new double[num_samples];

  // První průchod: měření a ukládání hodnot
  int index = 0;
  for (unsigned long f = f0; f <= f1; f += f2)
  {
    SetFreq(f);
    legacyAmPh2(measure_mag, measure_phase);

    magnitudes[index] = measure_mag;
    phases[index] = measure_phase;

    if (measure_mag > max_amplitude) {
      max_amplitude = measure_mag;
    }

    if (measure_phase > max_phase) {
      max_phase = measure_phase;
    }

    index++;
  }

  double phase_diff = max_phase - max_amplitude;

  // Druhý průchod: vypisování upravených hodnot
  for (int i = 0; i < num_samples; i++)
  {
    double corrected_phase = phases[i];
    // double corrected_phase = phases[i] - phase_diff;

    Serial.print(magnitudes[i]);
    Serial.print(";");
    Serial.print(corrected_phase);
    Serial.println();
  }

  // Uvolnění paměti
  delete[] magnitudes;
  delete[] phases;

  tempsensor.shutdown_wake(0);
  float temperature = tempsensor.readTempC();

  Serial.print(temperature);
  Serial.print(";");
  Serial.print(POT_VALUE);
  Serial.print(";");
  Serial.println("s");

  return 0;
}


void swap(int *p, int *q)
{
  int t;

  t = *p;
  *p = *q;
  *q = t;
}

double power(double base, int exponent){
  double res = 1;
  for (int k = 0; k < exponent; k++){
    res = res*base;
  }
  return res;
}

void sort(int a[], int n)
{
  int i, j;

  for (i = 0; i < n - 1; i++)
  {
    for (j = 0; j < n - i - 1; j++)
    {
      if (a[j] > a[j + 1])
        swap(&a[j], &a[j + 1]);
    }
  }
}

double preciseAmpl(unsigned long f)
{
  // uint64_t adcData = 0;
  // const int validReadings = AVERAGE_COUNT - (2 * DISCARD_COUNT);
  SetFreq(f);
  delayMicroseconds(WAIT_DELAY_US);

  // std::vector<int> values;
  std::vector<uint16_t> values;
  values.reserve(AVERAGE_COUNT);
  for (int i = 0; i < AVERAGE_COUNT; i++)
  {
    if (Italy) {
      values.push_back(analogRead(AD8302_MAG));
    }
    else {
      values.push_back((readADC() >> 32) & 0xFFFF);
    }
  }

  std::sort(values.begin(), values.end());
  std::vector<int> trimmed_samples(values.begin() + DISCARD_COUNT, values.end() - DISCARD_COUNT);
  double average = std::accumulate(trimmed_samples.begin(), trimmed_samples.end(), 0.0) / (AVERAGE_COUNT - 2 * DISCARD_COUNT);

  // long double cumsum = 0;
  // for (int i = DISCARD_COUNT; i < AVERAGE_COUNT - DISCARD_COUNT; i++)
  // {
  //   cumsum += values[i];
  // }

  return average; //cumsum / validReadings;
}

double precisePhase(long f)
{
  SetFreq(f);
  delayMicroseconds(WAIT_DELAY_US);

  // std::vector<int> values;
  std::vector<uint16_t> values;
  values.reserve(AVERAGE_COUNT);
  for (int i = 0; i < AVERAGE_COUNT; i++)
  {
    if (Italy) {
      values.push_back(analogRead(AD8302_PHASE));
    }
    else {
      values.push_back(readADC() & 0xFFFF);
    }
  }

  std::sort(values.begin(), values.end());
  std::vector<int> trimmed_samples(values.begin() + DISCARD_COUNT, values.end() - DISCARD_COUNT);
  double average = std::accumulate(trimmed_samples.begin(), trimmed_samples.end(), 0.0) / (AVERAGE_COUNT - 2 * DISCARD_COUNT);

  return average;
 
  // int x = AVERAGE_COUNT;

  // SetFreq(f);
  // delayMicroseconds(WAIT_DELAY_US);

  // double cumsum = 0;
  // for (int i = 0; i < x; i++)
  // {
  //   cumsum += analogRead(AD8302_PHASE);
  //   // cumsum += analogRead(AD8310_MAG);
  // }

  // return cumsum / (double)x;
}
/****************** FZU: HERE THE ORIGINAL FIRMWARE ENDS **************/
// 9999000;10001000;40
/**
 * move in steps towards boundary to the left
 */
long freq_boundary(long rf, double boundary, bool left)
{
  int x = left ? -1 : 1;
  long f = rf;
  int ampl = preciseAmpl(f);
  double b = (double)ampl * boundary;
  int step = 2048;

  // Serial.print("ampl: ");
  // Serial.println((double)ampl);

  // Serial.print("rf: ");
  // Serial.println(rf);

  // Serial.print("Boundary: ");
  // Serial.println((double)ampl * boundary);

  while (step > 3)
  {
    ampl = preciseAmpl(f + (step * x));
    // Serial.print("A: ");
    // Serial.println(ampl);
    // Serial.print("F: ");
    // Serial.println(f + (step * x));
    // delay(500);
    if (ampl > b)
    {
      f += (step * x);
    }
    else
    {
      step /= 2;
    }
  }

  // Serial.print("A: ");
  // Serial.println(ampl);
  // Serial.print("F: ");
  // Serial.println(f);
  return f;
}

const int DIRTY_NUM = 32;
const int DIRTY_RANGE = 16384;

/**
 * FZU: Find "dirty" maximum with really quick algorithm. We start with wide range and big steps. Then
 * we find maximum and start again with smaller interval and smaller steps. Algorithm ends when step is <= 1.
 */
long gradient1(long left_freq, long right_freq)
{
  double step_size = (right_freq - left_freq) / DIRTY_NUM;

  // recursion ends when step is too small
  if (step_size <= 1)
  {
    return left_freq + (DIRTY_NUM / 2) * step_size;
  }

  int a;
  int max_a = 0;
  int max_f = 0;

  // scan interval in given steps
  for (long f = left_freq; f <= right_freq; f += step_size)
  {
    a = preciseAmpl(f);
    // update current maximum
    if (a > max_a)
    {
      max_a = a;
      max_f = f;
    }
  }

  // run recursively again with smaller interval and smaller steps
  return gradient1(max_f - 2 * step_size, max_f + 2 * step_size);
}

long gradient2(long left_freq, long right_freq)
{
  double step_size = (right_freq - left_freq) / DIRTY_NUM;

  // recursion ends when step is too small
  if (step_size <= 0.5)
  {
    return left_freq + (DIRTY_NUM / 2) * step_size;
  }

  int a;
  int max_a = 0;
  int max_f = 0;

  // scan interval in given steps
  for (long f = left_freq; f <= right_freq; f += step_size)
  {
    a = precisePhase(f);
    // update current maximum
    if (a > max_a)
    {
      max_a = a;
      max_f = f;
    }
  }

  // run recursively again with smaller interval and smaller steps
  return gradient1(max_f - 2 * step_size, max_f + 2 * step_size);
}

long calib_freq = DEFAULT_CALIB_FREQ;

/**
 * FZU: when you know "dirty" resonant frequency, you scan frequencies
 * around the maximum and from the measured data calculate true resonant
 * frequency using polyfit.
 */

double sweepFrequency(long rf)
{
  // prepare variables
  //  String str = String();

  BLA::Matrix<SWEEP_COUNT> b;

  long f = rf - (SWEEP_RANGE / 2);

  // stabilize input, not measures anything
  preciseAmpl(f);

  // sweep around given frequency
  for (int i = 0; i < SWEEP_COUNT; i++, f += SWEEP_STEP)
  {
    // fill matrices and vectors for polyfit
    // use of preciseAmpl over PreciseAmplMedian is recommeded for
    b(i) = preciseAmpl(f);

    // cooldown frequency
    preciseAmpl(DEFAULT_CALIB_FREQ - 8000 + (DEFAULT_CALIB_FREQ - f));
  }

  BLA::Matrix<3> coeffs = A_dagger * b;

  quad_res = 0;
  for (int i = 0; i < SWEEP_COUNT; i++)
  {
    res = b(i) - (coeffs(0) * i * i + coeffs(1) * i + coeffs(2));
    quad_res += res * res;
  }
  quad_res = quad_res / SWEEP_COUNT;

  // calculate frequency from indexes
  double result = (0 - coeffs(1) / (2 * coeffs(0))) * (double)SWEEP_STEP + (double)rf - ((double)SWEEP_RANGE / 2);

  calib_freq = (long)result;

  return result;
}

double sweepFrequency5(long rf)
{
  // prepare variables
  //  String str = String();

  BLA::Matrix<SWEEP_COUNT> b;

  long f = rf - (SWEEP_RANGE / 2);

  // stabilize input, not measures anything
  preciseAmpl(f);

  // sweep around given frequency
  for (int i = 0; i < SWEEP_COUNT; i++, f += SWEEP_STEP)
  {
    // fill matrices and vectors for polyfit
    // use of preciseAmpl over PreciseAmplMedian is recommeded for
    b(i) = preciseAmpl(f);

    // cooldown frequency
    preciseAmpl(DEFAULT_CALIB_FREQ - 8000 + (DEFAULT_CALIB_FREQ - f));
  }

  BLA::Matrix<POLY_DEGREE> coeffs = B_dagger * b;
 
  // calculate frequency from indexes
  //double result = (0 - coeffs(1) / (2 * coeffs(0))) * (double)SWEEP_STEP + (double)rf - ((double)SWEEP_RANGE / 2);
  long max = 0;
  int max_i = 0;
  int x;
  double poly_val, polyval;
  int j;
  for (int i = 0; i<SWEEP_COUNT; i++){
      x = i/SWEEP_COUNT;
      poly_val = 0;
      for(int j = 0; j<= POLY_DEGREE; j++){
          polyval += coeffs(j)*power(x, j);
      }
      if(polyval > max){
        max = polyval;
        max_i = i;
      }
  }

  double result = rf - (SWEEP_RANGE / 2) + max_i*(double)SWEEP_STEP;

  calib_freq = (long)result;

  return result;
}

double sweepPhase(long rf)
{
  // not recommended because of phase curve shape - parabola doesn't fit well

  BLA::Matrix<SWEEP_COUNT> b;

  double contraction_factor = 30;
  long f = rf - (SWEEP_RANGE / 4);

  // stabilize input, not measures anything
  precisePhase(f);

  // sweep around given frequency
  for (int i = 0; i < SWEEP_COUNT; i++, f += double(SWEEP_STEP / contraction_factor))
  {
    // fill matrices and vectors for polyfit
    b(i) = precisePhase(f);

    // cooldown frequency
    precisePhase(DEFAULT_CALIB_FREQ - 8000 + (DEFAULT_CALIB_FREQ - f));
  }

  BLA::Matrix<3> coeffs = A_dagger * b;

  quad_res = 0;
  for (int i = 0; i < SWEEP_COUNT; i++)
  {
    res = b(i) - (coeffs(0) * i * i + coeffs(1) * i + coeffs(2));
    quad_res += res * res;
  }
  quad_res = quad_res / SWEEP_COUNT;

  // calculate frequency from indexes
  double result = (0 - coeffs(1) / (2 * coeffs(0))) * (double)SWEEP_STEP + (double)rf - ((double)SWEEP_RANGE / 2);

  calib_freq = (long)result;

  return result;
}

/**
 * FZU: calculate dissipation from given resonant frequency
 */
double dissipation(unsigned long rf)
{
  double dis = -1.0;

  // stabilize input
  SetFreq(rf);
  delayMicroseconds(WAIT_DELAY_US * 3);
  if (Italy) {
    analogRead(AD8302_MAG);
  }

  // second stabilization
  SetFreq(rf);
  if (WAIT)
    delayMicroseconds(WAIT_DELAY_US);

  unsigned long fl = rf;
  unsigned long fr = rf;
  int la = analogRead(AD8302_MAG);
  int ra = la;
  double boundary = (double)la * 0.707;
  int step = 2048;

  // move in steps towards 70.7% boundary for dissipation calc to the left
  while (step > 3 && la > 1000)
  {
    SetFreq(fl - step);
    if (WAIT)
      delayMicroseconds(WAIT_DELAY_US);

    la = analogRead(AD8302_MAG);
    if (la > boundary)
    {
      fl -= step;
    }
    else
    {
      step /= 2;
    }
  }

  // move in steps towards 70.7% boundary for dissipation calc to the right
  step = 2048;
  while (step > 3 && ra > 1000)
  {
    SetFreq(fr + step);
    if (WAIT)
      delayMicroseconds(WAIT_DELAY_US);

    ra = analogRead(AD8302_MAG);
    if (ra > boundary)
    {
      fr += step;
    }
    else
    {
      step /= 2;
    }
  }

  // calculate dissipation (maybe change to quality factor)
  dis = (double)(fr - fl) / (double)rf;

  if (dis * dis > 1)
  {
    dis = -1;
  }
  return dis;
}

/**
 * FZU: only for debugging purposes, don't really look at it.
 */
double sweepDebug(unsigned long rf)
{
  String str = String();
  BLA::Matrix<SWEEP_COUNT, 3> A;
  BLA::Matrix<SWEEP_COUNT> b;
  BLA::Matrix<DIS_COUNT> d;

  unsigned long f = rf - (DIS_RANGE / 2);
  double cumsum = 0;
  double max = 0, left = 0, right = 0;
  double maxf = -1.0;
  double dlf = -1.0;
  double drf = -1.0;
  double dis = -1.0;
  // int maxidx = -1;
  int ldis = -1;
  int rdis = -1;

  SetFreq(f);
  delayMicroseconds(WAIT_DELAY_US * 3);
  analogRead(AD8302_MAG);

  Serial.println(SWEEP_COUNT);
  Serial.println(SWEEP_STEP);

  for (int i = 0; i < DIS_COUNT; i++, f += DIS_STEP)
  {
    SetFreq(f);
    if (WAIT)
      delayMicroseconds(WAIT_DELAY_US);
    cumsum = 0;

    for (int j = 0; j < SWEEP_REPEAT; j++)
    {
      cumsum += analogRead(AD8302_MAG);
    }

    d(i) = cumsum / (double)SWEEP_REPEAT;

    if (i == 0) left = d(i);
    if (i == DIS_COUNT - 1) right = d(i);
    if (d(i) > max)
    {
      max = d(i);
      // maxidx = i;
      maxf = (double)f;
    }
  }

  if ((left / max < 0.7) && (right / max < 0.7)) {
    f = rf - (DIS_RANGE / 2);
    for (int i = 0; i < DIS_COUNT; i++, f += DIS_STEP)
    {
      if (ldis < 0 && d(i) > 0.707 * max)
      {
        ldis = i;
        dlf = (double)f;
      }
      if (ldis > 0 && rdis < 0 && d(i) < 0.707 * max)
      {
        rdis = i - 1;
        drf = (double)f;
        break;
      }
    }
    dis = maxf / (drf - dlf);
  }
  else {
    dis = -0.42;
  }
  Serial.println(dis);

  f = rf - (SWEEP_RANGE / 2);
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
    // A(i, 0) = i * i;
    // A(i, 1) = i;
    // A(i, 2) = 1;

    Serial.println(f);
    Serial.println(b(i));

    // if (b(i) < 3000)
    // {
    //   return -b(i); //-1;
    // }

    str.concat(b(i)).concat(';');
  }

  //  Serial.println(str);

  BLA::Matrix<3> coeffs = A_dagger * b;
  // BLA::Matrix<3> coeffs = ((~A) * A).Inverse() * (~A) * b;
  double result = (0 - coeffs(1) / (2 * coeffs(0))) * (double)SWEEP_STEP + (double)rf - ((double)SWEEP_RANGE / 2);

  Serial.println(coeffs(0));
  Serial.println(coeffs(1));
  Serial.println(coeffs(2));
  //  Serial.println(result);

  calib_freq = (long)result;

  return result;
}

/**
 * FZU: our version of firmware supports multiple commands
 */
int modernRead(String msg)
{
  // long param = msg.substring(2).toInt();
  char cmd = msg.charAt(0);
  unsigned long difTime, absTime, relTime;

  unsigned long f, fe, f0, f1, f2;
  double rf, rfph, rf30, rf30ph, rf50, rf50ph, dis, x;
  float t;
  int i, w, e, g;
  float temp = tempsensor.readTempC();
  byte count;

  double measure_phase = 0;
  double measure_mag = 0;
  int app_phase = 0;
  int app_mag = 0;

  int rf_cnt = 128;
  int rf_step = 40;
  long rf_hb = rf_cnt * rf_step / 2;

  // unsigned long f0 = 10002600;
  // unsigned long f1 = 10003200;
  // int f2 = 200;
  int mm = 0;

  switch (cmd)
  {

  case '1':
    digitalWrite(LED1, HIGH);
    sf = 9000000;
    temp = tempsensor.readTempC();
    Serial.print(sf);
    Serial.print(" Hz ... Teplota: ");
    Serial.print(temp);
    Serial.println(" °C");
    SetFreq(sf); // long frequency

    delay(500);
    digitalWrite(LED1, LOW);
    delay(500);
    break;

  case '2':
    digitalWrite(LED1, HIGH);
    sf = 10000000;
    // Serial.println("Jsem tady .... ");
    temp = tempsensor.readTempC();
    Serial.print(sf);
    Serial.print(" Hz ... Teplota: ");
    Serial.print(temp);
    Serial.println(" °C");
    SetFreq(sf); // long frequency

    delay(500);
    digitalWrite(LED1, LOW);
    delay(500);
    break;

  case '3':
    digitalWrite(LED1, HIGH);
    sf = 11000000;
    // Serial.println("Jsem tady .... ");
    temp = tempsensor.readTempC();
    Serial.print(sf);
    Serial.print(" Hz ... Teplota: ");
    Serial.print(temp);
    Serial.println(" °C");
    SetFreq(sf); // long frequency

    delay(500);
    digitalWrite(LED1, LOW);
    delay(500);
    break;

  case 'A':
    if (sf > 11000000) sf -= 10000000;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'S':
    sf -= 1000000;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'Q':
    sf -= 100000;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'W':
    sf -= 10000;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'E':
    sf -= 1000;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'Z':
    sf -= 100;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'X':
    sf -= 10;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'C':
    sf -= 1;
    if (sf < 1000000) sf = 1000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'V':
    sf += 1;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'B':
    sf += 10;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'N':
    sf += 100;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'T':
    sf += 1000;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'Y':
    sf += 10000;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'U':
    sf += 100000;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'F':
    sf += 1000000;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'G':
    sf += 10000000;
    if (sf > 60000000) sf = 60000000;
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    break;

  case 'H':
    SetFreq(sf);
    Serial.print(sf);
    Serial.print(" Hz, Am;Ph: ");
    legacyAmPh();
    Serial.println(WAIT_DELAY_US);
    break;

  case 'D': // only for debug
    // f = gradient1(calib_freq - DIRTY_RANGE, calib_freq + DIRTY_RANGE);
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    // rf = sweepFrequency(f);
    Serial.println(calib_freq - DIRTY_RANGE);
    Serial.println(calib_freq + DIRTY_RANGE);
    Serial.println(f);
    rf = sweepDebug(f);
    Serial.println(rf);
    Serial.println(WAIT_DELAY_US);
    Serial.println(AVERAGE_SAMPLE);
    tempsensor.shutdown_wake(0);
    t = tempsensor.readTempC();
    Serial.println(t);
    Serial.println("s");
    break;

  case 'c': // CALEX measurement for CARDAM
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency(f);
    Serial.println(rf);
    break;

  case 'd': // Debug for Cardam
    fe = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    f0 = fe - (256 * 40);
    f1 = fe + (256 * 40);
    f2 = 40;

    for (f = f0; f <= f1; f += f2)
    {
      SetFreq(f);
      if (WAIT) delayMicroseconds(WAIT_DELAY_US);
      if (WAIT_LONG) delay(10);

      app_phase = 0;
      app_mag = 0;

      for (i = 0; i < AVERAGE_SAMPLE; i++)
      {
        app_phase += analogRead(AD8302_PHASE);
        app_mag += analogRead(AD8302_MAG);
      }

      measure_phase = 1.0 * app_phase / AVERAGE_SAMPLE;
      measure_mag = 1.0 * app_mag / AVERAGE_SAMPLE;

      Serial.print(f);
      Serial.print(";");
      Serial.print(measure_mag);
      Serial.print(";");
      Serial.print(measure_phase);
      Serial.println();
    }
    break;

  case 'i':
    serializeJsonPretty(fw, Serial);
    Serial.println();
    break;

  case 'j': // only frequency measurement for Jakub 'case' algorithm
    x = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency(x);
    Serial.println(rf);
    break;

  case 'k': // only frequency measurement for Jakub 'case' algorithm
    x = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency5(x);
    Serial.println(rf);
    break;

  case 'm': // main measurement
    // f = gradient1(calib_freq - DIRTY_RANGE, calib_freq + DIRTY_RANGE);
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency(f);
    Serial.println(rf);
    dis = dissipation(rf);
    Serial.println(dis, 9);
    tempsensor.shutdown_wake(0);
    t = tempsensor.readTempC();
    Serial.println(t);
    break;

  case 'M': // only for debug
    // f = gradient1(calib_freq - DIRTY_RANGE, calib_freq + DIRTY_RANGE);
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency(f);
    Serial.println(rf);
    dis = dissipation(rf);
    Serial.println(dis, 9);
    tempsensor.shutdown_wake(0);
    t = tempsensor.readTempC();
    Serial.println(t);
    Serial.println("s");
    break;

  case 'n': // main measurement to json
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency(f);
    f = gradient2(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rfph = sweepPhase(f);
    f = gradient1(3*DEFAULT_CALIB_FREQ - 3*DIRTY_RANGE, 3*DEFAULT_CALIB_FREQ + 3*DIRTY_RANGE);
    rf30 = sweepFrequency(f);
    f = gradient2(3*DEFAULT_CALIB_FREQ - 3*DIRTY_RANGE, 3*DEFAULT_CALIB_FREQ + 3*DIRTY_RANGE);
    rf30ph = sweepFrequency(f);
    f = gradient1(5*DEFAULT_CALIB_FREQ - 5*DIRTY_RANGE, 5*DEFAULT_CALIB_FREQ + 5*DIRTY_RANGE);
    rf50 = sweepFrequency(f);
    f = gradient2(5*DEFAULT_CALIB_FREQ - 5*DIRTY_RANGE, 5*DEFAULT_CALIB_FREQ + 5*DIRTY_RANGE);
    rf50ph = sweepFrequency(f);
    data["id"] = ++dseq;
    data["frequency"] = rf;
    data["frequencyPhase"] = rfph;
    data["frequency30"] = rf30;
    data["frequency30Phase"] = rf30ph;
    data["frequency50"] = rf50;
    data["frequency50Phase"] = rf50ph;
    dis = dissipation(rf);
    data["dissipation"] = dis;
    tempsensor.shutdown_wake(0);
    t = tempsensor.readTempC();
    data["temperature"] = t;
    serializeJsonPretty(data, Serial);
    Serial.println();
    break;

  case 'r': // main measurement with resonance curves to json
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    rf = sweepFrequency(f);
    data["id"] = ++dseq;
    data["frequency"] = rf;
    dis = dissipation(rf);
    data["dissipation"] = dis;
    tempsensor.shutdown_wake(0);
    t = tempsensor.readTempC();
    data["temperature"] = t;
    for (long f = rf - rf_hb; f <= rf + rf_hb; f += rf_step)
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
      magValues.add(measure_mag);
      phaseValues.add(measure_phase);
    }
    serializeJsonPretty(data, Serial);
    Serial.println();
    magValues.clear();
    phaseValues.clear();
    break;

  case 'R':
    potval_str = msg.substring(1);
    if (POT_ADDRESS && potval_str.toInt() >= 0 && potval_str.toInt() < 256)
    {
      POT_VALUE = potval_str.toInt();
      Wire.beginTransmission(POT_ADDRESS);
      Wire.write(0x01);
      Wire.write(POT_VALUE);
      Wire.endTransmission();
    }
    break;

  case 's':
    Serial.printf("%u", teensyUsbSN());
    break;

  case 't':
    digitalWrite(LED1, HIGH);
    Serial.println("Test ...");
    delay(500);
    digitalWrite(LED1, LOW);
    delay(500);
    break;

  case 'v': // Viktor's debug
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);

    Serial.println(f);

    for (e = -200; e < 200; e++)
    {
      g = f + 4 * e;
      Serial.println(preciseAmpl(g));
      // cooldown frequency
      preciseAmpl(DEFAULT_CALIB_FREQ - 8000 + (DEFAULT_CALIB_FREQ - f));
    }

    break;

  case 'w': // Viktor's debug
    f = gradient1(DEFAULT_CALIB_FREQ - DIRTY_RANGE, DEFAULT_CALIB_FREQ + DIRTY_RANGE);
    // f = 10001241;
    Serial.println(f);
    delayMicroseconds(100);
    for (e = -200; e < 200; e++)
    {
      SetFreq(f + 4 * e);
      delayMicroseconds(WAIT_DELAY_US);
      for (w = 0; w < 100; w++)
      {
        Serial.println(analogRead(AD8302_MAG));
        delayMicroseconds(100);
      }
    }
    break;

  default:
    Serial.println("Konec ... ");
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

  // Serial.println("Modern: " + String(useModern));
  // Serial.println("RetVal: " + String(retVal));
}
