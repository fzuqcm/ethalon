/***********************************************************
 * FZU: This is a FZU version of QCM firmware. Some parts are not changed from the Italien one,
 * because it is only setting up the digital inputs and outputs.
 ***********************************************************/

/******************************* LIBRARIES *****************************/
/** FZU: YOU NEED TO INSTALL BasicLinearAlgebra LIBRARY FROM THE MENU **/
#include <Wire.h>
#include "src/Adafruit_MCP9808.h"
#include <ADC.h>
/*************************** DEFINE ***************************/
#define FW_NAME "FZU QCM Firmware"
#define FW_VERSION "3.00"
#define FW_DATE "14.01.2022"
#define FW_AUTHOR "Anonymous"

// potentiometer AD5252 I2C address is 0x2C(44)
#define ADDRESS 0x2D
// potentiometer AD5252 default value for compatibility with openQCM Q-1 shield @5VDC
// #define POT_VALUE 240 //254
// reference clock
//#define REFCLK 125000000
#define REFQ 12000000
#define USE_MULTIPLIER
#ifdef  USE_MULTIPLIER
#define  REFCLK (REFQ*6)
#else  
  #define REFCLK REFQ
#endif  

/*************************** VARIABLE DECLARATION ***************************/
// potentiometer AD5252 default value for compatibility with openQCM Q-1 shield @5VDC
int POT_VALUE = 240; //254
String potval_str = String(POT_VALUE);
// current input frequency
long freq = 0;
// DDS Synthesizer AD9851 pin function
int WCLK = A8;
int DATA = A9;
int FQ_UD = A1;
// frequency tuning word
unsigned long FTW;
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
int LED1 = 24;
int LED2 = 25;
int LED3 = 26;

// ADC init variabl
boolean WAIT = true;
// ADC waiting delay microseconds
// int WAIT_DELAY_US = 300;
int WAIT_DELAY_US = 100;
int AVERAGE_COUNT = 50;

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
  // float temp_FTW 
  temp_FTW = (frequency * pow(2, 32)) / REFCLK;
  Serial.print(temp_FTW);
  Serial.print(" - ");
  FTW = (unsigned long)temp_FTW;
  Serial.print("f: ");
  Serial.print(frequency);
  Serial.print(" CFW: ");
  Serial.print(FTW, DEC);
  Serial.print(" - ");
  Serial.print(FTW, HEX);
  Serial.print(" - ");
  Serial.println(FTW, BIN);
  long pointer = 1;
  int pointer2 = 0b10000000;
  #ifdef  USE_MULTIPLIER
    int lastByte = 0b10000000;
  #else  
    int lastByte = 0b00000000;
  #endif  
  

  #define DELAY 1 
  /* 32 bit dds tuning word frequency instructions */
  for (int i = 0; i < 32; i++)
  {
    if ((FTW & pointer) > 0)
      digitalWrite(DATA, HIGH);
    else
      digitalWrite(DATA, LOW);
    digitalWrite(WCLK, HIGH);
    delayMicroseconds(DELAY);
    digitalWrite(WCLK, LOW);
    delayMicroseconds(DELAY);
    pointer = pointer << 1;
  }

  /* 8 bit dds phase and x6 multiplier refclock*/
  for (int i = 0; i < 8; i++)
  {
    if ((lastByte & pointer2) > 0) digitalWrite(DATA, HIGH);
    else digitalWrite(DATA, LOW);
    //digitalWrite(DATA, LOW);
    
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
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  digitalWrite(LED1, HIGH);
  digitalWrite(LED2, HIGH);
  digitalWrite(LED3, HIGH);
  delay(500);
  digitalWrite(LED1, LOW);
  digitalWrite(LED2, LOW);
  digitalWrite(LED3, LOW);

  while (!Serial)
  {

    ; // wait for serial port to connect. Needed for native USB port only
  }
}


double preciseAmpl(long f)
{
  int x = AVERAGE_COUNT;

  SetFreq(f);
  delayMicroseconds(WAIT_DELAY_US);
  
  long double cumsum = 0;
  for (int i = 0; i < x; i++)
  {
    cumsum += analogRead(AD8302_MAG);
    //delayMicroseconds(5);
  }

  return cumsum / (double)x;
}



double precisePhase(long f)
{
  int x = AVERAGE_COUNT;

  SetFreq(f);
  delayMicroseconds(WAIT_DELAY_US);

  double cumsum = 0;
  for (int i = 0; i < x; i++)
  {
    cumsum += analogRead(AD8302_PHASE);
  }

  return cumsum / (double)x;
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
  return gradient1(max_f -  2* step_size, max_f + 2 * step_size);
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
  return gradient1(max_f -  2* step_size, max_f + 2 * step_size);
}

//long calib_freq = DEFAULT_CALIB_FREQ;

/**
 * FZU: when you know "dirty" resonant frequency, you scan frequencies 
 * around the maximum and from the measured data calculate true resonant
 * frequency using polyfit.
 */

/*************************** LOOP ***************************/
void loop()
{
  //if (!(Serial.available() > 0))
  //{
  //  return;
  //}

  //String msg = Serial.readStringUntil('\n');
  digitalWrite(LED1, HIGH);
  float temp = tempsensor.readTempC();
  Serial.print("Teplota: ");
  Serial.print(temp);
  Serial.println(" °C");
  SetFreq(10000000); //long frequency
  
  delay(500);
  digitalWrite(LED1, LOW);
  delay(500);
  // Serial.println("Modern: " + String(useModern));
  // Serial.println("RetVal: " + String(retVal));
}
