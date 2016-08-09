from __future__ import absolute_import

from jobs.app import app

@app.task
def add(x, y):
    return x + y

@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)

if __name__=="__main__":
    print add.delay(2,3)
    