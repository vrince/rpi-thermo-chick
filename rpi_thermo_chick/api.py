
import RPi.GPIO as GPIO

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import uvicorn
import click

import datetime
import json
from typing import Optional
from threading import Thread
from time import sleep
from random import randrange
from os import environ, path
from appdirs import user_config_dir

host = environ.get('RPI_THERMO_CHICK_HOST', '0.0.0.0')
port = environ.get('RPI_THERMO_CHICK_PORT', '8000')
config_dir = user_config_dir('rpi-thermo-chick')
module_dir = path.dirname(__file__)

app = FastAPI()
vue_app = open( module_dir + '/index.html', 'r').read()

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

def update_min_max_temperature():
    global thermometers
    for i, _ in enumerate(thermometers):
        thermometers[i]['min'] = min([e for e in histories[i] if e is not None])
        thermometers[i]['max'] = max([e for e in histories[i] if e is not None])

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
            update_min_max_temperature()
            push_history(histories)
        apply_thermostat()
        sleep(30)

def pull_history():
    with open(config_dir + '/histories.json', 'r') as f:
        return json.load(f)

def push_history(h):
    with open(config_dir + '/histories.json', 'w') as f:
        json.dump(h, f)

# state
ts = now_ts()
init = False
stopped = False
interval = 15*60 # 15 min in sec 
intervalPerDay = 24*4 #number of interval (15min) per day
target_temperature = 5

config = {}
with open(config_dir + '/config.json', 'r') as f:
    config = json.load(f)

# read mendatory relay / thermometers info
relays = config['relays']
thermometers = config['thermometers']

# init the rest
for r in relays:
    r.update({'on':0, 'ts': now_ts()})
for t in thermometers:
    t.update({'temp':0, 'ts': now_ts(), 'min': 0, 'max': 0})

# read back historical data
histories = []
try:
    histories = pull_history()
    update_min_max_temperature()
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
        'rpi-thermo-chick': '🐔🔥',
        'ok': True,
        'relays': relays, 
        'thermometers': thermometers,
        'ts': ts,
        'index': index, 
        'target_temperature': target_temperature
        }

@app.get('/app', response_class=HTMLResponse)
def read_vue_app():
    #return open(module_dir + '/index.html', 'r').read()
    return vue_app

@app.get('/relay/{relay_id}/{action}')
def read_item(relay_id: int, action: str = 'on'):

    valid_ids = range(0, len(relays)-1)

    if relay_id not in valid_ids:
        return  {'ok': False, 'msg': f'relay_id must be in {valid_ids}'}

    if action not in ['on','off']:
        return  {'ok': False, 'msg': 'action must be \'on\' or \'off\''}

    set_relay(relay_id, GPIO.HIGH if action == 'on' else GPIO.LOW)
    return {'ok': True, 'relays': relays}

@app.get('/chart')
def read_history():
    return {
        'rpi-thermo-chick': '🐔🔥',
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
    
@click.command()
@click.option('--host', default='0.0.0.0', help='Host (default 0.0.0.0) [env RPI_THERMO_CHICK_HOST]')
@click.option('--port', default=8000,   help='Port (default 8000) [env RPI_THERMO_CHICK_PORT]')
def cli(host, port):
    """
    rpi-thermo-chick: 🐔🔥
    """
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    cli(auto_envvar_prefix='RPI_THERMO_CHICK')