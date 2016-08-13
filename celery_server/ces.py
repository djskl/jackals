from datetime import datetime
from time import sleep
import random

def f():
    print datetime.now().strftime("%M:%S"), "1--------------------------------1"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------2"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------3"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------4"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------5"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------6"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------7"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------8"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------9"
    sleep(random.randint(0,5))
    print datetime.now().strftime("%M:%S"), "1--------------------------------10"
    
if __name__=="__main__":
    f()
