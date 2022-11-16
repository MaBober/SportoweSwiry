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
    import datetime as dt

    events = Event.query.all()
    log =[]

    for event in events:

        if event.start > dt.date.today():
            log.append((event.name, "Nie rozpoczęło się 0"))
            event.status = '0'

        elif event.start <= dt.date.today() and event.start + dt.timedelta(7) > dt.date.today():
            log.append((event.name, "Pierwszy tydzień 1"))
            event.status = '1'

        elif event.start + dt.timedelta(7) <= dt.date.today() and event.end + dt.timedelta(-6) > dt.date.today():
            log.append((event.name, "W trakcie 2"))
            event.status = '2'

        elif event.end + dt.timedelta(-6) <= dt.date.today() and dt.date.today() <= event.end:
            log.append((event.name, "Ostatni tydzień 3"))
            event.status = '3'

        elif event.end < dt.date.today() and dt.date.today() <= event.end + dt.timedelta(7):
            log.append((event.name, "Tydzień po 4"))
            event.status = '4'

        else:
            log.append((event.name, "zakończone! 5"))
            event.status = '5'

        db.session.commit()


    return str(log)