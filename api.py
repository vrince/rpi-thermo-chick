
import RPi.GPIO as GPIO

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import datetime
from typing import Optional
from threading import Thread
from time import sleep
from random import randrange

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")
vue_app = open("index.html", "r").read()

def now():
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

# temperature update
def update_temperature():
    global thermometers, histories, stopped, ts, interval, intervalPerDay, index
    ts = now()
    index = get_history_index(datetime.datetime.now(),interval, intervalPerDay)
    while not stopped:
        for i, t in enumerate(thermometers):
            temp = read_temperature(t['device'])
            if temp is not None:
                thermometers[i]['temp'] = temp
                thermometers[i]['ts'] = now()
                histories[i][index] = temp
        sleep(30)

ts = now()
init = False
stopped = False
interval = 15*60 #15 min in sec
intervalPerDay = 24*4 #number of interval (15min) per day
relays = [
    {'pin':4, 'on':0, 'ts': now()},
    {'pin':17,'on':0, 'ts': now()}]
thermometers = [
    {'temp':0, 'loc':'in', 'device': '28-3c01d075db96', 'ts': now()},
    {'temp':0, 'loc':'out', 'device': '28-3c01d0751fcd', 'ts': now()}]
histories = [
    [None] * intervalPerDay,
    [None] * intervalPerDay
]

print(histories)

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
    return {'thermo-chick': '🐤+🔥', 
    'relays': relays, 
    'thermometers': thermometers,
    'ts': ts,
    'index': index, 
    'histories': histories}

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

    relays[relay_id]['on'] = GPIO.HIGH if action == 'on' else GPIO.LOW
    relays[relay_id]['ts'] = now()
    GPIO.output(relays[relay_id]['pin'], relays[relay_id]['on'])

    return {"ok": True, 'relays': relays}

@app.get('/chart')
def read_history():
    return {'thermo-chick': '🐤+🔥', 
    'ts': ts,
    'index': index,
    'labels': [ f'{int(i/4)}h' if i % 4 == 0 else '' for i in range(intervalPerDay,0,-1)],
    'datasets': [rotate(histories[0], index+1), rotate(histories[1], index+1)]}
