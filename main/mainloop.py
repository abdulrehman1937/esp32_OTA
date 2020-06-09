import time
import gc
from initSystem import initSensor,create_jwt,get_mqtt_client,getSensorData
import machine
import esp32
import myos.path
import os
from ota_updater import OTAUpdater
publish_delay = 10000
fall_delay = 200
    # connect()
def on_message(topic, message):
    global publish_delay
    global fall_delay 
    topic=str(topic.decode("utf-8"))
    print((topic, message))
    if topic=='/devices/esp32_fall/commands/update':
        print("launching update after reboot")
        machine.reset()
    elif topic=='/devices/esp32_fall/commands/reboot':
        machine.reset()
    elif topic=='/devices/esp32_fall/commands/reset':
        try:
            os.remove("errors.log")
            print("deleted log file")
        except:
            print("Error file not exist")
        try:
            os.remove("config")
            print("deleted config file")
        except:
            print("config file not exist")
        try:
            os.remove("wifi.dat")
            print("deleted wifi file")
        except:
            print("wifi file not exist")
        machine.reset()
    elif topic=='/devices/esp32_fall/commands/myconfig':
        f1 = open(myos.path.dirname(__file__) + '/../config','w')
        message=str(message.decode("utf-8"))
        f1.write(message)
        f1.close()
        message=message.split()
        publish_delay=int(message[0])
        fall_delay=int(message[1])
        print("Done updateing and writing"+str(publish_delay)+str(fall_delay))
        
    
def startloop(config):
    global publish_delay
    global fall_delay
    publish_delay = 3000
    fall_delay = 200
    print("hi updated here 1")
    try:
        f = open(myos.path.dirname(__file__) + '/../config','r')
        temp=str(f.readline())
        print(temp)
        publish_delay=int(temp)
        temp=str(f.readline())
        print(temp)
        fall_delay=temp
        f.close()
        #os.remove("confif")
        print("Done updateing"+str(publish_delay)+str(fall_delay))
        del f
    except:
        print("Config file not presnt")
        
        
    lastMillisFall = 0
    lastMillis = 0
    sendData = ""    
    led_pin = machine.Pin(config.device_config['led_pin'], machine.Pin.OUT)
    gc.collect()
    initSensor()
    jwt = create_jwt(config.google_cloud_config['project_id'], config.jwt_config['private_key'],config.jwt_config['algorithm'], config.jwt_config['token_ttl'])
        # sendData.append(getSensorData())
    client = get_mqtt_client(config.google_cloud_config['project_id'], config.google_cloud_config['cloud_region'],config.google_cloud_config['registry_id'], config.google_cloud_config['device_id'], jwt,on_message,config.google_cloud_config['mqtt_bridge_hostname'],config.google_cloud_config['mqtt_bridge_port'])
    millis = time.ticks_ms()
    gc.collect()
        # sendData.append(getSensorData())
    publish_delay = 3000
    fall_delay = 200
    time.sleep(1)
    try:
        f = open(myos.path.dirname(__file__) + '/../errors.log','r')
        msg=f.read()
        print(msg)
        print("Publishing Erros log messages "+str(len(msg)))
        mqtt_topic = '/devices/{}/{}'.format(
                config.google_cloud_config['device_id'], 'events')
        client.publish(mqtt_topic.encode('utf-8'),
                msg.encode('utf-8'))
        f.close()
        os.remove("erros.log")
        print("File Removed!")
        del f
        del msg
    except:
        print("file not exists")

    time.sleep(1)
    gc.collect()
    try:
        while True:
            if time.ticks_ms()-lastMillis > publish_delay:
                lastMillis = time.ticks_ms()
                print(len(sendData))
                # print("\n".join(sendData))

                print(gc.mem_free())
                gc.collect()
                """
                message = {
                    "device_id": config.google_cloud_config['device_id'],
                    "sensor": 
                }
                """

                print(gc.mem_free())
                # sendData=[]
                gc.collect()
                print(gc.mem_free())
                print("Publishing message "+str(len(sendData)))
                led_pin.value(1)
                mqtt_topic = '/devices/{}/{}'.format(
                    config.google_cloud_config['device_id'], 'events')
                client.publish(mqtt_topic.encode('utf-8'),
                               sendData.encode('utf-8'))
                gc.collect()
                del sendData
                sendData = ""
                led_pin.value(0)

            if time.ticks_ms()-lastMillisFall > fall_delay:
                lastMillisFall = time.ticks_ms()
                gc.collect()
                #print("Adding data"+str(gc.mem_free()))
                sendData = getSensorData()+"\n"+sendData
                gc.collect()
                #print(gc.mem_free())

            client.check_msg()  # Check for new messages on subscription
            # utime.sleep(10)  # Delay for 10 seconds.
    except Exception as e:
        print("Here")
        
        e=str(e)
        print(e)
        error="Error"
        print("saving errors log")
        f1 = open(myos.path.dirname(__file__) + '/../errors.log','w')
        f1.write(e)
        f1.write("\n")
        f1.close()
        print("saved errors log")
        led_pin.value(0)
        time.sleep(10)
        machine.reset()

