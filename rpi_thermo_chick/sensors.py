import os
import logging
from random import random

logger = logging.getLogger('rpi.thermo.chick')

if not os.path.exists('/sys/bus/w1'):
    logger.warning('one wire not found/install temperature data will be random')


def read_temperature(device: str) -> float:

    device_path = f'/sys/bus/w1/devices/{device}/w1_slave'

    if not os.path.exists(device_path):
        fake_temperature = 35*random() - 10
        logger.debug(f'using ramdom temperature {fake_temperature}')
        return fake_temperature
    
    with open(f'/sys/bus/w1/devices/{device}/w1_slave', 'r') as f:
        lines = f.readlines()
        while lines[0].strip()[-3:] != 'YES':
            return None
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temperature = lines[1][equals_pos+2:]
            return float(temperature) / 1000.0
    return None