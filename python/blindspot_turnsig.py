import RPi.GPIO as GPIO
import time

# Pin Definitons:
led_turnl =  33  #left turn signal pin 33
led_turnr =  7   #right turn signal pin 7
led_sigl =  15  #left warning pin 15
led_sigr =  19 #right warning pin 19
switch_pinl = 24    # Board pin 24 as left switch
switch_pinr = 26    # board pin 26 as right switch



def main():

    prev_valuel = None
    prev_valuer = None
    # Pin Setup:
    GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme
    GPIO.setup(led_turnl, GPIO.OUT)  # left turn blinker set as output
    GPIO.setup(led_turnr, GPIO.OUT)  # right turn blinker  set as output
    GPIO.setup(led_sigl, GPIO.OUT)   #left warning 
    GPIO.setup(led_sigr, GPIO.OUT)    #right warning

    GPIO.setup(switch_pinl, GPIO.IN)  # left switch pin set as input
    GPIO.setup(switch_pinr, GPIO.IN)  # right switch pin set as input
    


    # Initial state for LEDs:
    GPIO.output(led_turnl, GPIO.LOW)   #turn signal left off
    GPIO.output(led_turnr, GPIO.LOW)   #turn signal right off
    GPIO.output(led_sigl, GPIO.LOW)    #warning light left off
    GPIO.output(led_sigr, GPIO.LOW)   #warning light right off
    


    print("Starting blindspot object detection")
    try:
        while True:
            curr_valuel = GPIO.input(switch_pinl)   #sets curr_valuel as left turn signal status
            curr_valuer = GPIO.input(switch_pinr)   #sets curr_valuer as right turn signal status
            if curr_valuel != prev_valuel:          # checks for a left switch change
                GPIO.output(led_turnl, GPIO.HIGH)
                GPIO.output(led_sigl, GPIO.HIGH)
                prev_valuel = curr_valuel
            elif curr_valuer != prev_valuer:   #checks right switch change 
                GPIO.output(led_turnr,GPIO.HIGH)
                GPIO.output(led_sigr,GPIO.HIGH)   
                prev_valuer = curr_valuer
            time.sleep(1)

    finally:
        GPIO.cleanup()  # cleanup all GPIOs

if __name__ == '__main__':
    main()
