#!/usr/bin/python3
# python 3.6

import random
import time
import smbus

from paho.mqtt import client as mqtt_client

# MQTT settings
broker = '127.0.0.1'
port = 1883
#topic = "python/mqtt"
topic = "domoticz/in"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'yourusername'
password = 'yourpassword'

# Sensors settings
# Lux min and max value incase of a sensor error
min = 0
max = 40000
# name and id of dummy lux sensor in Domoticz
id_name = 'Lux Aquarium : '
idx_list = '4452'



def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def getlux(id):
   # Get I2C bus
   bus = smbus.SMBus(1)
   # TSL2561 address, 0x39(57)
   # Select control register, 0x00(00) with command register, 0x80(128)
   #        0x03(03)    Power ON mode
   try:
      bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
   except IOError:
      bus.write_byte_data(0x29, 0x00 | 0x80, 0x03)
      #print "Oops! Error  Try again..."
   # TSL2561 address, 0x39(57)
   # Select timing register, 0x01(01) with command register, 0x80(128)
   #        0x02(02)    Nominal integration time = 402ms
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


def publish(client):
    while True:
        lux = getlux(id)
        # filter lux min and max value incase of a sensor error
        if lux >= min and lux <= max:
            #msg = f"messages: {msg_count}"
            begin_sl_char = "{"
            end_sl_char = "}"
            msg = f"{begin_sl_char}\"idx\" : {idx_list}, \"svalue\" : \"{str(lux)}\"{end_sl_char}"
            result = client.publish(topic, msg)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{topic}`")
            else:
                print(f"Failed to send message to topic {topic}")
    time.sleep(1)


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)


if __name__ == '__main__':
    run()
