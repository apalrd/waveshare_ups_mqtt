#Copyright (C) 2022 Andrew Palardy
#See LICENSE file for complete license terms

#Client to publish INA219 data from a Waveshare UPS board to MQTT
#Useful if you use these boards, maybe, hopefully
#Anyway, use the file /etc/waveshare_ups.yaml to configure this thing
#Good luck

import time
import yaml
import json
from paho.mqtt import client as mqtt_client
from INA219 import INA219
import platform
import threading
from datetime import datetime


#Main routine
def Main():
    #Load config.yaml
    CFName = "/etc/waveshare_ups.yaml"
    print("CONFIG: Opening file ",CFName)
    CFile = open(CFName,'r')
    Config = yaml.safe_load(CFile)

    #For debugging, print the whole thing
    print("CONFIG: The entire configuration structure is ",Config)

    #Get hostname for later
    Hostname = platform.node()
    print("CONFIG: Hostname is",Hostname)

    #Read UPS section to see which model it is
    ConfigUPS = Config.get('ups')
    if ConfigUPS is None:
        print("UPS: Section not configured in yaml")
        exit()
    ConfigUPSModel = ConfigUPS.get('model')
    if ConfigUPSModel is None:
        print("UPS: Model is not selected in yaml")
        exit()

    #Read UPS address or set to default
    ConfigUPSAddr = ConfigUPS.get('addr')
    
    #Initialize UPS or error if invalid model
    UPS = None
    if ConfigUPSModel == "32V_2A":
        if ConfigUPSAddr is None:
            ConfigUPSAddr = 0x42
        UPS = INA219(addr=ConfigUPSAddr)
        UPS.set_calibration_32V_2A()
        print("UPS: Configured INA219 at address",ConfigUPSAddr,"for 32V 2A")
    elif ConfigUPSModel == "16V_5A":
        if ConfigUPSAddr is None:
            ConfigUPSAddr = 0x43
        UPS = INA219(addr=ConfigUPSAddr)
        UPS.set_calibration_16V_5A()
        print("UPS: Configured INA219 at address",ConfigUPSAddr,"for 16V 5A")
    else:
        print("UPS: Unrecognized UPS model \"",ConfigUPSModel,"\"")
        exit()

    #Connect to MQTT broker
    ConfigMQTT = Config.get('mqtt')
    if ConfigMQTT is None:
        print("MQTT: Section not configured in yaml")
        exit()

    Broker = ConfigMQTT.get('broker')
    if Broker is None:
        print("MQTT: Broker is not configured in yaml")
        exit()

    #Get optional fields
    Port = ConfigMQTT.get('port',1883)
    Prefix = ConfigMQTT.get('prefix','ups')
    Uname = ConfigMQTT.get('username')
    Pword = ConfigMQTT.get('password')

    #Merge prefix and hostname to get the topic
    Topic = Prefix + "/" + Hostname
    print("MQTT: Topic is",Topic)

    #Create the broker connection
    Client = mqtt_client.Client(Topic)

    #If username and password are set, then set them
    if Uname is not None:
        if Pword is None:
            print("MQTT: Username is valid, but password is None")
            print("MQTT: Not using authentication")
        else:
            Client.username_pw_set(Uname,Pword)

    #Last Will and Testament
    Client.will_set(Topic,"{\"Status\": 0}",0,True)

    #MQTT print on connect
    def on_connect(client,userdata,flags,rc):
        print("MQTT: Connected")

    Client.on_connect = on_connect

    #Connect
    Client.connect(Broker, Port)


    #MQTT task
    def task():
        print("MQTT: Started Task")
        Client.loop_forever(retry_first_connection=True)

    #Start a new task for MQTT
    ClientThread = threading.Thread(target=task,name='MQTT',args=())
    ClientThread.start()

    #Initially set last values to -1
    DataLast = None
    TimeLast = datetime.now()

    #Get update data from config
    UpdateRate = ConfigUPS.get('update_rate',30)
    UpdateCur = ConfigUPS.get('update_cur',0.1)
    UpdateVolt = ConfigUPS.get('update_volt',0.1)
    UpdatePct = ConfigUPS.get('update_pct',5)

    #Loop forever
    while(1):
        try:
            Data = {'Status':1}
            #Get all data from the INA219
            Data['VoltBus'] = UPS.getBusVoltage_V()             # voltage on V- (load side)
            Data['VoltShunt'] = UPS.getShuntVoltage_mV() / 1000 # voltage between V+ and V- across the shunt
            Data['VoltPSU'] = Data['VoltBus'] + Data['VoltShunt']
            Data['Cur'] = UPS.getCurrent_mA() / 1000            # current in A
            Data['Power'] = UPS.getPower_W()                    # power in W
            #This percentage comes from the Waveshare code, blame them for inaccuracy
            Data['Pct'] = (Data['VoltBus'] - 6)/2.4*100
            if(Data['Pct'] > 100):Data['Pct'] = 100
            if(Data['Pct'] < 0):Data['Pct'] = 0

            #Current time
            TimeNow = datetime.now()
            Data['LastUpdate'] = TimeNow.strftime("%Y-%m-%d-%H:%M:%S")

            #Decide if we should send an update
            Update = False

            #Update if DataLast is none (first call)
            if DataLast is None:
                DataLast = Data
                Update = True
                TimeLast = TimeNow

            #Update if it's been at least UpdateRate seconds
            if (TimeNow - TimeLast).total_seconds() >= UpdateRate:
                Update = True


            #Update if current, voltage, or percent is outside of update limits
            if (abs(Data['Cur'] - DataLast['Cur']) >= UpdateCur) or           \
               (abs(Data['VoltBus'] - DataLast['VoltBus']) >= UpdateVolt) or  \
               (abs(Data['Pct'] - DataLast['Pct']) >= UpdatePct):
                Update=True


            #If we should publish an update
            if Update:
                #Publish data
                Client.publish(Topic,json.dumps(Data))
                #Store data for next time
                DataLast = Data
                TimeLast = TimeNow

            #Wait a second
            time.sleep(1)
        except:
            print("Exception taken")
            break

    #Stop threads
    print("Exiting")
    ClearStatus = Client.publish(Topic,"{\"Status\":0}",0,True)
    print("Waiting for exit message to publish")
    ClearStatus.wait_for_publish()
    Client.disconnect()


#Entry point
if __name__ == "__main__": 
    Main() 