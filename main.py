#   Halkin Maksim

import time
print("ESP32 GSM Controll Module")

time.sleep(2)

import machine
import mpgsm



i=0
try:

    mpgsm.device.MainWavecom()
    i+=1
except KeyboardInterrupt as e:
    print("main.py except KeyboardInterrupt")
    machine.reset()
except Exception:
    print("main.py except Exception")
    machine.reset()


