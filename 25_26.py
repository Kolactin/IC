import machine
import utime
led=machine.Pin(2,machine.Pin.OUT)
Button=machine.Pin(5,machine.Pin.IN,machine.Pin.PULL_DOWN)

while(True):
  if Button.value() == 1:
    led.value(1)
  utime.sleep(0.1)