# rpi-thermo-chick 🔥+🐤

## Hardware

Raspberry Pi
Sensor DS18B20 using `1-wire`
Relay

## OS preparation

Enable `1-wire` : 

Add following lines to your `/boot/config.txt`: 

```ini
[all]
dtoverlay=w1-gpio,gpiopin=27 
# default pin is 4 but it enter in conflict with relay hat
```

```bash
sudo reboot
# when rebooted, check is module is loaded with
lsmod | grep -i w1_
```

## References

[1-wire](https://pinout.xyz/pinout/1_wire#)
[Adafruits lesson 11](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing)