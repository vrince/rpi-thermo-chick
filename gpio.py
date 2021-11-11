import RPi.GPIO as GPIO
from time import sleep
from random import randint, choice

pins = [4,17]
states = [GPIO.LOW,GPIO.HIGH]

GPIO.setmode(GPIO.BCM)
[GPIO.setup(pin, GPIO.OUT) for pin in pins]

try:
    while True:
        pin = choice(pins)
        state = choice(states)
        print(f'{pin}:{state}')
        GPIO.output(pin, state)
        sleep(60)
except:
    pass

print("cleanup")
GPIO.output(pin, GPIO.LOW)
GPIO.cleanup()
