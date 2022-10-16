
import logging

logger = logging.getLogger('rpi.thermo.chick')

skip_relay_control = False
try:
    import RPi.GPIO as GPIO
except:
    logger.warning('GPIO not found, will skip relay control')
    skip_relay_control = True


def init_gpio(relays):

    if skip_relay_control:
        logger.debug('skipping init_gpio')
        return

    GPIO.setmode(GPIO.BCM)
    for _,relay in enumerate(relays):
        GPIO.setup(relay['pin'], GPIO.OUT)
        GPIO.output(relay['pin'], GPIO.LOW)


def set_relay(relay_pin, state):

    if skip_relay_control:
        logger.debug(f'skipping relay pin({relay_pin}) set({state})')
        return

    gpio_state = GPIO.HIGH if state == 1 else GPIO.LOW
    GPIO.output(relay_pin, gpio_state)