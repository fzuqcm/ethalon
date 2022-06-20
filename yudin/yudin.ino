/***********************************************************
 * FZU: This is a FZU version of firmware. Some parts are not changed from the Italien one,
 * because it is only setting up the digital inputs and outputs.
 ***********************************************************/

/******************************* LIBRARIES *****************************/
/** FZU: YOU NEED TO INSTALL BasicLinearAlgebra LIBRARY FROM THE MENU **/
#include <BasicLinearAlgebra.h>
#include <Wire.h>
#include "src/Adafruit_MCP9808.h"
#include <ADC.h>
#include "QuickMedianLib.h"
#include <math.h>


/*************************** DEFINE ***************************/
// potentiometer AD5252 I2C address is 0x2C(44)
#define ADDRESS 0x2C
// potentiometer AD5252 default value for compatibility with openQCM Q-1 shield @5VDC
// #define POT_VALUE 240 //254
// reference clock
#define REFCLK 125000000

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


const int DEFAULT_CALIB_FREQ = 10000000;
const int DEFAULT_RANGE = 65536;

const int SWEEP_STEP = 32;
const int SWEEP_RANGE = 1024;
const int SWEEP_COUNT = SWEEP_RANGE / SWEEP_STEP + 1;
const int SWEEP_REPEAT = 16;

const int DIS_STEP = 256;
const int DIS_RANGE = 16384;
const int DIS_COUNT = DIS_RANGE / DIS_STEP + 1;

BLA::Matrix<3, SWEEP_COUNT> A_dagger;
BLA::Matrix<SWEEP_COUNT, 3> A;
double quad_res;
double res;

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

  for (int i = 0; i < SWEEP_COUNT; i++)
  {
    A(i, 0) = i * i;
    A(i, 1) = i;
    A(i, 2) = 1;
  }

  A_dagger = ((~A) * A).Inverse() * (~A);

  while (!Serial)
  {

    ; // wait for serial port to connect. Needed for native USB port only
  }

}

void swap(int* xp, int* yp){
    int temp = *xp;
    *xp = *yp;
    *yp = temp;
}
// Function to perform Selection Sort
void selectionSort(int arr[], int n)
{
    int i, j, min_idx;
 
    // One by one move boundary of unsorted subarray
    for (i = 0; i < n - 1; i++) {
 
        // Find the minimum element in unsorted array
        min_idx = i;
        for (j = i + 1; j < n; j++)
            if (arr[j] < arr[min_idx])
                min_idx = j;
 
        // Swap the found minimum element
        // with the first element
        swap(&arr[min_idx], &arr[i]);
    }
}

int firsttime = 0;
void loop()
{

long arrived = 0;

  if (Serial.available() > 0) {
    
    int vals[51];
    long mean = 0;
    
    if (firsttime != 0) {
      String msg = Serial.readStringUntil('\n');
      //Serial.println(msg);
      int len = msg.length();
      for (int i=0; i<len; i++) {
        arrived *= 10;
        arrived += (msg[i] - '0');
      }

      SetFreq(arrived);
      Serial.println(arrived);

      //collect 51 values
      for (int i=0; i<51; i++) {
        vals[i] = analogRead(AD8302_MAG);
        //Serial.print(vals[i]);
        //Serial.print(", ");
        mean += vals[i];
        delayMicroseconds(100);
      }

      //calculate mean 
      mean = mean/51;
      
      //order vals
      selectionSort(vals,51);
      int med = vals[25];   //median is here

      double sd = 0;
      for (int i=0; i<51; i++) {
        sd += pow(vals[i]-mean,2);
      }
      sd = sqrt(sd/51);

      Serial.println(med);
      Serial.println(mean);
      Serial.println(sd);
      
      
    }
    
    else {
      firsttime = 1;
      int x;
      String msg = Serial.readStringUntil('\n');
      int len = msg.length() - 1;
      for (int i=0; i<len; i++) {
        arrived *= 10;
        arrived += (msg[i] - '0');
      }
    //ARRIVED hold freq to be set
      SetFreq(arrived);
      for (int i=0; i<59; i++) {
        delayMicroseconds(100);
        x = analogRead(AD8302_MAG);
      }
    }
    //FIRST RUN FINISHED HERE
  }
}