#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
 
RF24 radio(PB0, PA4); // CE, CSN on Black Pill 
const uint64_t address = 0xF0F0F0F0E1LL;
int counter = 0;
 
void setup() 
{
Serial.begin(9600);
radio.begin();                  
radio.openWritingPipe(address); 
radio.setPALevel(RF24_PA_MIN);  
radio.stopListening();          //This sets the module as transmitter
}
 
void loop()
{
char text[] = " Hello World";
char str[50];
sprintf(str,"%s %d",text,counter);
radio.write(&str, sizeof(str));  
 
Serial.println(str);
counter++;
delay(2000);
}
