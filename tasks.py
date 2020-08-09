from celery import Celery
from script import Temp
app = Celery()
app.config_from_object("celery_settings")


@app.task()
def task(access_code):
    cool = Temp(access_code)
    return "hello"