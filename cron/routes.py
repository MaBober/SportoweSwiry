import datetime as dt
import csv

from flask_login import login_required, current_user
from start import db, app
from flask import Blueprint, render_template, redirect, url_for, flash, request


cron = Blueprint("cron", __name__,
    template_folder='templates')

@cron.route("/cron/test", methods = ['POST'])
def cron_test_post():

    with open("cron_users.txt", "a") as file:
        file.write('dad' +"\n")

    return "crom"

@cron.route("/cron/update_events_statuses", methods = ['POST'])
def cron_update_event_statuses():

    from event.classes import Event

    events = Event.query.all()
    log =[]

    for event in events:

        event.update_status()

    return str(log)