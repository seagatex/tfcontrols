#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_linear_poti import BrickletLinearPoti
from tinkerforge.bricklet_distance_ir import BrickletDistanceIR
from tinkerforge.bricklet_dual_button import BrickletDualButton
from subprocess import call
import time, json, os, thread
import paho.mqtt.client as mqtt


# TinkerForge stuff
HOST = "localhost"
PORT = 4223
UID_LP = "fyV" # Change to your UID
UID_BTN = "mMV" # Change to your UID
UID_IR = "ju5" # Change to your UID

ipcon = IPConnection() # Create IP connection
lp = BrickletLinearPoti(UID_LP, ipcon) # Create device object
ir = BrickletDistanceIR(UID_IR, ipcon) # Create device object
db = BrickletDualButton(UID_BTN, ipcon) # Create device object


# MQTT stuff
client = mqtt.Client()
loop = False

previousValue_lp = 0
previousValue_btn = 0
previousValue_ir = 0

def send_data():
    global senseHat
    global client
    global lp,ir
    global previousValue_lp
    global previousValue_ir

    # Get current position (range is 0 to 100)
    position_lp = lp.get_position()
    if (position_lp != previousValue_lp):
        print("Position: " + str(position_lp))
        #Publish the values over mqtt
        client.publish("tinkerforge/linear_pot", position_lp,1,True)
        previousValue_lp = position_lp

    # Get current position (range is 0 to 100)
    position_ir = ir.get_distance()
    ir_treshold = 5
    ir_max = 600
    if (position_ir > ir_max): position_ir = ir_max
    if ((position_ir == ir_max and previousValue_ir != position_ir) or (position_ir > previousValue_ir+ir_treshold or position_ir < previousValue_ir-ir_treshold)):
        print("Distance: " + str(position_ir))
        #Publish the values over mqtt
        client.publish("tinkerforge/distance_ir", position_ir,1,True)
        previousValue_ir = position_ir


# Callback function for state changed callback
button_l_old = 0
button_r_old = 0
def cb_state_changed(button_l, button_r, led_l, led_r):
    global button_l_old, button_r_old
    if (button_l == db.BUTTON_STATE_PRESSED and button_l_old != 1):
           print("Left button pressed")
           client.publish("tinkerforge/dual_button/left",1,1,True)
           button_l_old = 1
    elif (button_l == db.BUTTON_STATE_RELEASED and button_l_old != 0):
           print("Left button released")
           client.publish("tinkerforge/dual_button/left",0,1,True)
           button_l_old = 0

    if (button_r == db.BUTTON_STATE_PRESSED and button_r_old != 1):
        print("Right button pressed")
        client.publish("tinkerforge/dual_button/right", 1,1,True)
        button_r_old = 1
    elif (button_r == db.BUTTON_STATE_RELEASED and button_r_old != 0):
        print("Right button released")
        client.publish("tinkerforge/dual_button/right", 0 ,1,True)
        button_r_old = 0


def on_connect(client, userdata, flags, rc):
    global ipcon
    ipcon.connect(HOST, PORT) # Connect to brickd
    # Don't use device before ipcon is connected

    thread.start_new_thread(measure_loop,())

def on_disconnect(client, userdata, flags):
    global loop
    loop = False
    print("[" + time.strftime('%x %X') + "] DISCONNECT")


def measure_loop():
    global loop, client
    try:
        if (not loop):
            loop = True
            while (loop):
                send_data()
                time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        client.disconnect()
        ipcon.disconnect()
        pass


db.register_callback(db.CALLBACK_STATE_CHANGED, cb_state_changed)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect("mqtt.virit.in")
client.loop_forever(10,1,True)
