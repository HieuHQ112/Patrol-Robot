import Jetson.GPIO as GPIO
import time
led_pin=7
GPIO.setmode(GPIO.BOARD)
GPIO.setup(led_pin, GPIO.OUT, initial=GPIO.HIGH)

while 1:
    time.sleep(2)
    GPIO.output(led_pin, GPIO.HIGH)   
    time.sleep(2)
    GPIO.output(led_pin, GPIO.LOW)   
