#!/usr/bin/python
#--------------------------------------
#
# Script for updating to Domoticz
#
# Author : Vincent Rouwhorst
# Date   : 27/09/2021
#
# Domoticz Json documentation
# https://www.domoticz.com/wiki/Domoticz_API/JSON_URL's#Custom_Sensor
#--------------------------------------

import requests
import smbus
import time

DOMOTICZ_IP = 'http://127.0.0.1:8080'

def getlux(id):
   # Get I2C bus
   bus = smbus.SMBus(1)
   # TSL2561 address, 0x39(57)
   # Select control register, 0x00(00) with command register, 0x80(128)
   #		0x03(03)	Power ON mode
   try:
      bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
   except IOError:
      bus.write_byte_data(0x29, 0x00 | 0x80, 0x03)
      #print "Oops! Error  Try again..."
   # TSL2561 address, 0x39(57)
   # Select timing register, 0x01(01) with command register, 0x80(128)
   #		0x02(02)	Nominal integration time = 402ms
   try:
      bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)
   except IOError:
      bus.write_byte_data(0x29, 0x01 | 0x80, 0x02)

   time.sleep(5)

   # Read data back from 0x0C(12) with command register, 0x80(128), 2 bytes
   # ch0 LSB, ch0 MSB
   try:
      data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)
   except IOError:
      data = bus.read_i2c_block_data(0x29, 0x0C | 0x80, 2)
   # Read data back from 0x0E(14) with command register, 0x80(128), 2 bytes
   # ch1 LSB, ch1 MSB
   #data1 = bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)

   # Convert the data
   ch0 = data[1] * 256 + data[0]
   #ch1 = data1[1] * 256 + data1[0]

   # Output data to screen
   #print "Full Spectrum(IR + Visible) :%d lux" % ch0
   #print "Infrared Value :%d lux" % ch1
   #print "Visible Value :%d lux" % (ch0 - ch1)
   return int(ch0)

if __name__ == '__main__':
  # Script has been called directly

  # Lux min and max value incase of a sensor error
  min = 0
  max = 40000
  # name and id of dummy lux sensor in Domoticz
  id_name = 'Lux Aquarium : '
  idx_list = '4452'

  while True:
      try:
          #print id_name + getlux(id)
          lux = getlux(id)
          #print('lux : ', lux)
          # filter temp min and max value incase of a sensor error
          if lux >= min and lux <= max:
              print(DOMOTICZ_IP + "/json.htm?type=command&param=udevice&idx=" + idx_list + "&svalue=" + str(lux))
              r = requests.get(DOMOTICZ_IP + "/json.htm?type=command&param=udevice&idx=" + idx_list + "&svalue=" + str(lux))
              siteresponse = r.json()
              #if siteresponse["status"] == 'OK':
                  #print('Response = OK')
	      if siteresponse["status"] == 'ERR':
                  # Write ERROR to Domoticz log
                  message = "ERROR writing sensor " + id_name
		  #print(message)
		  requests.get(DOMOTICZ_IP + "/json.htm?type=command&param=addlogmessage&message=" + message)
      except ValueError:
           print "Oops! Error  Try again..."
