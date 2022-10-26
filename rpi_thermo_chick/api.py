from ast import Str
from dataclasses import fields
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

import uvicorn
import click

import datetime
import json
from threading import Thread
from time import sleep
from os import environ, path
from appdirs import user_config_dir
from pydantic import BaseModel
from importlib.metadata import version

from rpi_thermo_chick import logger
from rpi_thermo_chick.sensors import read_temperature
from rpi_thermo_chick.relays import init_gpio, set_relay
from rpi_thermo_chick.influxdb import init_influxdb_client, write_to_influxdb, query_mean, is_influxdb_ready

host = environ.get('RPI_THERMO_CHICK_HOST', '0.0.0.0')
port = environ.get('RPI_THERMO_CHICK_PORT', '8000')
config_dir = user_config_dir('rpi-thermo-chick')
module_dir = path.dirname(__file__)

app = FastAPI( title="rpi-thermo-chick",
    description='Thermostat for chicken 🐔🔥',
    version=version('rpi-thermo-chick'),
    terms_of_service="http://example.com/terms/",
    license_info={
        "name": "MIT",
    },)
vue_app = open( module_dir + '/index.html', 'r').read()

def now_ts():
    return datetime.datetime.now().isoformat()

def apply_thermostat():
    inside_temp = thermometers[0]['temp']
    if inside_temp < target_temperature:
        update_relay(0, 1)
    elif inside_temp >= target_temperature + 1:
        update_relay(0, 0)

def update():
    global thermometers, histories, ts, index
    while not stopped:
        ts = now_ts()
        fields = {}
        for i, t in enumerate(thermometers):
            temp = read_temperature(t['device'])
            fields[thermometers[i].get('name',str(i))] = temp
            if temp is not None:
                thermometers[i]['temp'] = temp
                thermometers[i]['ts'] = now_ts()
        write_to_influxdb(name="temperature_sensors", fields=fields, bucket=config.influxdb.bucket, org=config.influxdb.org)
        apply_thermostat()
        tags = {'id': 0}
        fields = {'on': int(relays[0]['on'])}
        write_to_influxdb(name="relays", fields=fields, tags=tags, bucket=config.influxdb.bucket, org=config.influxdb.org)
        sleep(config.period)


def update_relay(relay_id, state):
    relays[relay_id]['on'] = state
    relays[relay_id]['ts'] = now_ts()
    set_relay(relays[relay_id]['pin'], state)


class Relay(BaseModel):
    pin: int

class Thermometer(BaseModel):
    name: str
    device: str

class Influxdb(BaseModel):
    url: str = 'http://localhost:8086'
    bucket: str = 'bucket'
    org: str = 'org'
    token: str

class Config(BaseModel):
    relays: List[Relay]
    thermometers: List[Thermometer]
    influxdb: Influxdb = None
    period: int = 30


# state
ts = now_ts()
initialized = False
stopped = False
target_temperature = 5
config = None
relays = []
thermometers = []

def init(config_file=''):
    global config, relays, thermometers, initialized, influxdb
    if not config_file:
        config_file = config_dir + '/config.json'
    config = Config.parse_file(config_file)

    # read mandatory relay / thermometers info
    relays = config.dict()['relays']
    thermometers = config.dict()['thermometers']

    # read optional
    init_influxdb_client(config.influxdb)

    # init the rest
    for r in relays:
        r.update({'on':0, 'ts': now_ts()})
    for t in thermometers:
        t.update({'temp':0, 'ts': now_ts()})

    # setup GPIO
    if not initialized:
        initialized = True
        init_gpio(relays)

def start():
    # start temp update loop
    thread = Thread(target=update, name='temperature-loop')
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
        'target_temperature': target_temperature
        }

@app.get('/app', response_class=HTMLResponse)
def get_vue_app():
    return open(module_dir + '/index.html', 'r').read()
    #return vue_app

@app.get('/relay/{relay_id}/{action}')
def set_relay_action(relay_id: int, action: str = 'on'):
    valid_ids = range(0, len(relays)-1)
    if relay_id not in valid_ids:
        return  {'ok': False, 'msg': f'relay_id must be in {valid_ids}'}
    if action not in ['on','off', '1', '0']:
        return  {'ok': False, 'msg': 'action must be \'on\' or \'off\''}

    update_relay(relay_id, 1 if action in ['on', '1'] else 0)
    return {'ok': True, 'relays': relays}

@app.get('/chart')
def get_chart_data(window: str = '15m', range: str = '24h'):
    if not is_influxdb_ready:
        raise HTTPException(status_code=404, detail="influxdb is missing")
    bucket = config.influxdb.bucket
    org = config.influxdb.org
    timestamp, inside = query_mean(name='temperature_sensors', field='inside', 
        window=window, range=range, 
        bucket=bucket, org=org)
    _, outside = query_mean(name='temperature_sensors', field='outside', 
        window=window, range=range, 
        bucket=bucket, org=org)
    _, relay = query_mean(name='relays', field='on',
        window=window, range=range, 
        bucket=bucket, org=org)
    return {
        'rpi-thermo-chick': '🐔🔥',
        'ok': True,
        'ts': ts,
        'labels': timestamp,
        'datasets': [inside[:len(timestamp)], outside[:len(timestamp)], [int(r * 100) for r in relay][:len(timestamp)]]
        }

@app.get('/target/{temperature}')
def set_target_temperature(temperature: int):
    global target_temperature
    target_temperature = max(2,min(temperature,30))
    apply_thermostat()
    return {'ok': True, 'relays': relays}
    
@click.command()
@click.option('--host', default='0.0.0.0', help='Host (default 0.0.0.0) [env RPI_THERMO_CHICK_HOST]')
@click.option('--port', default=8000, help='Port (default 8000) [env RPI_THERMO_CHICK_PORT]')
@click.option('--config-file', default=f'{config_dir}/config.json', help='Config file [env RPI_THERMO_CHICK_CONFIG]')
def cli(host, port, config_file):
    """
    rpi-thermo-chick: 🐔🔥
    """
    init(config_file)
    start()
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    cli(auto_envvar_prefix='RPI_THERMO_CHICK')