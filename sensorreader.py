import smbus2
import bme280
import time
import datetime
import RPi.GPIO as GPIO
import os
from elasticsearch import Elasticsearch

#sensor setup
port = 1
address = 0x76
bus = smbus2.SMBus(port)
calibration_params = bme280.load_calibration_params(bus, address)

#relay setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(20,GPIO.OUT)
GPIO.setup(26,GPIO.OUT)
GPIO.setup(21,GPIO.OUT)

def time_now(): #function for timestamp
    time_is = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") #format date time string
    return time_is

#Set up file paths
path = os.path.dirname(os.path.realpath(__file__)) #find current file path
ini_file = path + "/" + 'override.ini' #specify override.ini file
log_file_path = path + "/" + 'sensorreader.log' #specify log output file


#logger
output_to_log = False
log_file = open(log_file_path, 'a+') #open log
log_file.write(str(time_now()) + "---Sensor reader started---\n") #welcome message in log
log_file.close() #close log

# define Elasticsearch address
es=Elasticsearch([{'host':'libreelec','port':9200}])

# get es time
def es_time():
    utctime = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    return utctime

while True:
    #sensor
    data = bme280.sample(bus, address, calibration_params)
    sensortime = str(data.timestamp)
    temperature = round(data.temperature, 3)
    pressure = round(data.pressure, 3)
    humidity = round(data.humidity, 3)
    print(sensortime)
    print("The Temperature is: " + str(temperature))
    print("The Pressure is: " + str(pressure))
    print("The Humidity is: " + str(humidity))
    print("\n")
    
    #relay
    
    if humidity > 60:
        GPIO.output(21,True)
    else:
        GPIO.output(21,False)

    # build elasticsearch payload
    es_payload={
        "Time":es_time(),
        "Temperature": temperature,
        "Pressure": pressure,
        "Humidity": humidity,
      }
    
    if output_to_log:
        log_file = open(log_file_path, 'a+') #open log
        log_file.write(str(time_now()) + "\n")
        log_file.write("The Temperature is: " + str(temperature) + "\n")
        log_file.write("The Pressure is: " + str(pressure) + "\n")
        log_file.write("The Humidity is: " + str(humidity) + "\n")
        log_file.close() #close log
    else:
        pass

    # send payload to elasticsearch
    try:
        res = es.index(index='livingroom', doc_type='_doc', body=es_payload)
    except:
        print("\n" + " Error Sending to ElasticSearch, ignoring...")

    #sleep
    time.sleep(60)