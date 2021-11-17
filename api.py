
import RPi.GPIO as GPIO

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import datetime
import json
from typing import Optional
from threading import Thread
from time import sleep
from random import randrange

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")
vue_app = open("index.html", "r").read()

def now_ts():
    return datetime.datetime.now().isoformat()

def read_temperature(device: str) -> float:
    with open(f'/sys/bus/w1/devices/{device}/w1_slave', 'r') as f:
        lines = f.readlines()
        while lines[0].strip()[-3:] != 'YES':
            return None
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temperature = lines[1][equals_pos+2:]
            return float(temperature) / 1000.0
    return None

def get_history_index(date, interval, intervalPerDay):
    seconds_since_midnight = (date - date.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    return max(0,min(int(seconds_since_midnight / interval), intervalPerDay))

def rotate(arr,d):
    result = arr[d:len(arr)]+arr[0:d]
    return result

def set_relay(relay_id, state):
    relays[relay_id]['on'] = state
    relays[relay_id]['ts'] = now_ts()
    GPIO.output(relays[relay_id]['pin'], state)

def apply_thermostat():
    inside_temp = thermometers[0]['temp']
    if inside_temp < target_temperature:
        set_relay(0, GPIO.HIGH)
    elif inside_temp >= target_temperature + 1:
        set_relay(0, GPIO.LOW)

# temperature update
def update_temperature():
    global thermometers, histories, ts, index
    now = datetime.datetime.now()
    last_push = now
    while not stopped:
        ts = now_ts()
        now = datetime.datetime.now()
        index = get_history_index(now,interval, intervalPerDay)
        for i, t in enumerate(thermometers):
            temp = read_temperature(t['device'])
            if temp is not None:
                thermometers[i]['temp'] = temp
                thermometers[i]['ts'] = now_ts()
                histories[i][index] = temp
                if (now - last_push).total_seconds() > 120:
                    last_push = now
                    push_history(histories)
        apply_thermostat()
        sleep(30)

def pull_history():
    with open('histories.json', 'r') as f:
        return json.load(f)

def push_history(h):
    with open('histories.json', 'w') as f:
        json.dump(h, f)

# state
ts = now_ts()
init = False
stopped = False
interval = 15*60 # 15 min in sec 
intervalPerDay = 24*4 #number of interval (15min) per day
target_temperature = 5
relays = [
    {'pin':4, 'on':0, 'ts': now_ts()},
    {'pin':17,'on':0, 'ts': now_ts()}]
thermometers = [
    {'temp':0, 'loc':'in', 'device': '28-3c01d075db96', 'ts': now_ts()},
    {'temp':0, 'loc':'out', 'device': '28-3c01d0751fcd', 'ts': now_ts()}]

# read back historical data
histories = []
try:
    histories = pull_history()
except:
    histories = [[None] * intervalPerDay, [None] * intervalPerDay]
    push_history(histories)

# setup GPIO
if not init:
    init = True
    GPIO.setmode(GPIO.BCM)
    for i,relay in enumerate(relays):
        GPIO.setup(relay['pin'], GPIO.OUT)
        GPIO.output(relay['pin'], GPIO.LOW)

# start temp update loop
thread = Thread(target=update_temperature, name='temperature-loop')
thread.setDaemon(True)
thread.start()

# server
@app.get('/')
def read_root():
    return {
        'thermo-chick': '🐤+🔥',
        'ok': True,
        'relays': relays, 
        'thermometers': thermometers,
        'ts': ts,
        'index': index, 
        'target_temperature': target_temperature
        }

@app.get('/app', response_class=HTMLResponse)
def read_vue_app():
    return open("index.html", "r").read()

@app.get('/bastien', response_class=HTMLResponse)
def read_vue_app():
    return open("bastien-index.html", "r").read()

@app.get('/relay/{relay_id}/{action}')
def read_item(relay_id: int, action: str = 'on'):

    if relay_id not in [0,1]:
        return  {"ok": False, "msg": "relay_id must be 0 or 1"}

    if action not in ["on","off"]:
        return  {"ok": False, "msg": "action must be 'on' or 'off'"}

    set_relay(relay_id, GPIO.HIGH if action == 'on' else GPIO.LOW)
    return {"ok": True, 'relays': relays}

@app.get('/chart')
def read_history():
    return {
        'thermo-chick': '🐤+🔥',
        'ok': True,
        'ts': ts,
        'index': index,
        'labels': [ f'{int(i/4)}h' if i % 4 == 0 else '' for i in range(intervalPerDay,0,-1)],
        'datasets': [rotate(histories[0], index+1), rotate(histories[1], index+1)]
        }

@app.get('/target/{temperature}')
def set_target_temperature(temperature: int):
    global target_temperature
    target_temperature = max(2,min(temperature,30))
    apply_thermostat()
    return {'ok': True, 'relays': relays}
    