from typing import Optional

import RPi.GPIO as GPIO

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import datetime

app = FastAPI()
vue_app = open("index.html", "r").read()

def now():
    return datetime.datetime.now().isoformat()

init = False
relays = [{'pin':4, 'on':0, 'ts': now()},{'pin':17,'on':0, 'ts': now()}]
thermometers = [{'temp':0, 'loc':'in', 'device': ''},{'temp':0, 'loc':'out', 'device': ''}]

# setup GPIO
if not init:
    init = True
    GPIO.setmode(GPIO.BCM)
    for i,relay in enumerate(relays):
        GPIO.setup(relay['pin'], GPIO.OUT)
        GPIO.output(relay['pin'], GPIO.LOW)

@app.get('/')
def read_root():
    return {'thermo-chick': '🐤+🔥', 'relays': relays, 'thermometers': thermometers}

@app.get('/app', response_class=HTMLResponse)
def read_vue_app():
    return open("index.html", "r").read()

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