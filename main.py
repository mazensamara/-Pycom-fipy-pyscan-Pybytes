# Copyright (c) 2020, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
# See https://docs.pycom.io for more information regarding library

import machine
import struct
import time
import pycom
from socket import socket
import socket
import ubinascii
from pycoproc_1 import Pycoproc
from MFRC630 import MFRC630
from LIS2HH12 import LIS2HH12
from LTR329ALS01 import LTR329ALS01
from machine import ADC
from network import LoRa
from network import WLAN
from machine import RTC
from machine import I2C
from _pybytes import Pybytes
from _pybytes_config import PybytesConfig

# Make sure heartbeat is disabled before setting RGB LED
pycom.heartbeat(False)

# Pybytes
conf = PybytesConfig().read_config()
pybytes = Pybytes(conf)
pybytes.start()
pybytes_enabled = True
if 'pybytes' in globals():
    if(pybytes.isconnected()):
        print('Pybytes is connected, sending signals to Pybytes')
        pybytes_enabled = True


# pycom.heartbeat(False)
pycom.rgbled(0x7f7f00) # Yellow
pyscan = Pycoproc(Pycoproc.PYSCAN)


# Connect to wifi
wlan = WLAN(mode=WLAN.STA)
wlan.connect(ssid='YOUR SSID', auth=(WLAN.WPA2, 'YOUR PASSWORD'))
while not wlan.isconnected():
    machine.idle()
time.sleep(1)
print('\n')
print("WiFi connected succesfully to :")
print(wlan.ifconfig())
pycom.rgbled(0xffffff)
time.sleep(5)


# setup rtc (time)
rtc = machine.RTC()
#time.timezone(-5000)
#adjust your local timezone, by default, NTP time will be GMT
#time.timezone(-18000) #we are located at GMT+2, thus 2*60*60
rtc.ntp_sync(server = "pool.ntp.org")
time.sleep(5)
print('\n')
print('\nRTC Set from NTP to UTC:', rtc.now())
time.timezone(-14200)
print('Adjusted from UTC to EST timezone', time.localtime(), '\n')
print(time.localtime())
# print(rtc.now())
a = rtc.synced()
print('RTC is synced to "pool.ntp.org": ', a)


#add your card UID here
VALID_CARDS = [[0x43, 0x95, 0xDD, 0xF8],
               [0x43, 0x95, 0xDD, 0xF9],
               [0x46, 0x5A, 0xEB, 0x7D, 0x8A, 0x08, 0x04]]


# This is the default key for an unencrypted MiFare card
CARDkey = [ 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]
DECODE_CARD = False

py = Pycoproc(Pycoproc.PYSCAN)
nfc = MFRC630(py)
lt = LTR329ALS01(py)
li = LIS2HH12(py)


RGB_BRIGHTNESS = 0x8

RGB_RED = (RGB_BRIGHTNESS << 16)
RGB_GREEN = (RGB_BRIGHTNESS << 8)
RGB_BLUE = (RGB_BRIGHTNESS)

counter = 0

def check_uid(uid, len):
    return VALID_CARDS.count(uid[:len])


# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915)


# Get device info
print('\n')
print("** DevEUI: %s" % (ubinascii.hexlify(lora.mac())))

# Uncomment for US915 / AU915 & Pygate
for i in range(0,8):
    lora.remove_channel(i)
for i in range(16,65):
    lora.remove_channel(i)
for i in range(66,72): 
    lora.remove_channel(i)

# join a network using OTAA (Over the Air Activation)
app_eui = ubinascii.unhexlify('YOUR app_eui')
app_key = ubinascii.unhexlify('YOUR app_key')
#uncomment to use LoRaWAN application provided dev_eui
dev_eui = ubinascii.unhexlify('YOUR dev_eui')  
#uncomment below to use LoRaWAN application provided dev_eui
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_eui, app_key), timeout=0)


# Read Battery voltage
print('\n')
print('** Battery voltage: ', py.read_battery_voltage())

# Accelerometer
li = LIS2HH12(py)
print('\n\n** 3-Axis Accelerometer (LIS2HH12)')
print("Acceleration: " + str(li.acceleration()))
print("Roll: " + str(li.roll()))
print("Pitch: " + str(li.pitch()))

# Light sensor
light = LTR329ALS01(py)
print('\n\n** Digital Ambient Light Sensor (LTR-329ALS-01)')
print("Light (channel Blue, channel Red): " + str(lt.light())," Lux: ", str(lt.lux()), "lx")

# Card Reader
nfc.mfrc630_cmd_init()

print('\n')
print('Scanning for cards')
while True:
    pycom.rgbled(0x00FF00)
    time.sleep(2)

    # Read Battery voltage
    print('\n')
    print('** Battery voltage: ', py.read_battery_voltage())
    pybytes.send_signal(1, py.read_battery_voltage())

    # Accelerometer
    li = LIS2HH12(py)
    print('\n\n** 3-Axis Accelerometer (LIS2HH12)')
    print("Acceleration: " + str(li.acceleration()))
    print("Roll: " + str(li.roll()))
    print("Pitch: " + str(li.pitch()))
    pybytes.send_signal(4, li.acceleration()[0])
    pybytes.send_signal(5, li.acceleration()[1])
    pybytes.send_signal(6, li.acceleration()[2])
    pybytes.send_signal(7, li.roll())
    pybytes.send_signal(8, li.pitch())

    # Light sensor
    print('\n\n** Digital Ambient Light Sensor (LTR-329ALS-01)')
    print("Light (channel Blue, channel Red): " + str(lt.light())," Lux: ", str(lt.lux()), "lx")
    pybytes.send_signal(2, lt.light())
    pybytes.send_signal(3, lt.lux())


    # Initialise the MFRC630 with some settings
    # Card Reader
    nfc.mfrc630_cmd_init()
    print('\n\n** Card Reader (RDIF, NFC) (MFRC630)')
    print('Scanning for cards ...')

    # Send REQA for ISO14443A card type
    atqa = nfc.mfrc630_iso14443a_WUPA_REQA(nfc.MFRC630_ISO14443_CMD_REQA)
    if (atqa != 0):
        # A card has been detected, read UID
        print('A card has been detected, reading its UID ...')
        uid = bytearray(10)
        uid_len = nfc.mfrc630_iso14443a_select(uid)
        print('UID has length {}'.format(uid_len))
        if (uid_len > 0):
            # A valid UID has been detected, print details
            counter += 1
            print("%d\tUID [%d]: %s" % (counter, uid_len, nfc.format_block(uid, uid_len)))
            if DECODE_CARD:
                # Try to authenticate with CARD key
                nfc.mfrc630_cmd_load_key(CARDkey)
                for sector in range(0, 16):
                    if (nfc.mfrc630_MF_auth(uid, nfc.MFRC630_MF_AUTH_KEY_A, sector * 4)):
                        pycom.rgbled(RGB_GREEN)
                        # Authentication was sucessful, read card data
                        readbuf = bytearray(16)
                        for b in range(0, 4):
                            f_sect = sector * 4 + b
                            len = nfc.mfrc630_MF_read_block(f_sect, readbuf)
                            print("\t\tSector %s: Block: %s: %s" % (nfc.format_block([sector], 1), nfc.format_block([b], 1), nfc.format_block(readbuf, len)))
                    else:
                        print("Authentication denied for sector %s!" % nfc.format_block([sector], 1))
                        pycom.rgbled(RGB_RED)
                # It is necessary to call mfrc630_MF_deauth after authentication
                # Although this is also handled by the reset / init cycle
                nfc.mfrc630_MF_deauth()
            else:
                #check if card uid is listed in VALID_CARDS
                if (check_uid(list(uid), uid_len)) > 0:
                    print('Card is listed, turn LED green')
                    pycom.rgbled(RGB_GREEN)
                    if(pybytes_enabled):
                        pybytes.send_signal(1, ('Card is listed', uid))
                else:
                    print('Card is not listed, turn LED red')
                    pycom.rgbled(RGB_RED)
                    if(pybytes_enabled):
                        pybytes.send_signal(1, ('Unauthorized card detected', uid))

    else:
        time.sleep(10)
        pycom.rgbled(0x0000FF)
        print('\nNo Card Detected')
        print('\n** Sleeping for 10 sec')
        print("Time and date: ", time.localtime())
        print("IP configuration: ", wlan.ifconfig())
        # We could go into power saving mode here... to be investigated
        nfc.mfrc630_cmd_reset()
        time.sleep(10)
        # Re-Initialise the MFRC630 with settings as these got wiped during reset
        nfc.mfrc630_cmd_init()

print(time.localtime())
time.sleep(5)
py.setup_sleep(10)
py.go_to_sleep()
