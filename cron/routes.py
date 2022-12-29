import datetime as dt
import csv
import os

from flask_login import login_required, current_user
from start import db, app
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app


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
    log = []

    for event in events:

        event.update_status()

    return str(log)

@cron.route("/cron/send_event_start_reminder", methods = ['POST'])
def cron_send_event_start_reminder():

    from event.classes import Event
    from user.classes import User
    from other.functions import send_email
    from config import Config

    if request.form['key'] != Config.CRON_KEY:
        current_app.logger.warning(f"Event end reminder cron job requested with wrong key!")
        return 'Access Denied!'

    current_app.logger.info(f"Event start reminder cron job requested with correct key")

    events = Event.query.all()
    for event in events:

        if event.start == dt.date.today():
            current_app.logger.info(f"Event {event.name} starts today. Reminders will be sent.")
            for user in event.give_all_event_users('Objects'):
                send_email(user.mail, f"Wyzwanie {event.name} rozpoczyna się dzisiaj!",'emails/event_start', event = event)

    return "Start event mails sent"



@cron.route("/cron/send_weekly_summary", methods = ['POST'])
def cron_send_weekly_summary():

    from user.classes import User
    from other.functions import send_email
    
    summary = StatisticalSummary(7)
    admins = User.all_application_admins()
    user = User.query.filter(User.id == "MaBober").first()

    #send_email(user.mail, f"Podsumowanie ostatnich {summary.days} dni",'emails/app_summary', summary = summary, admin = user)

    for admin in admins:
        send_email(admin.mail, f"Podsumowanie ostatnich {summary.days} dni",'emails/app_summary', summary = summary, admin = admin)

    return f'''New activities: {str(summary.new_activities)}
              New users: {str(summary.new_users)}
              New events: {str(summary.new_events)}
              Sumary for : {str(summary.start_date)} - {str(summary.end_date)}
              Admins: {str(admins)}'''
              
@cron.route("/cron/error_summary", methods = ['POST'])
def cron_errors_summary():

    report = generate_error_summary(7)

    return report

def generate_error_summary(days = 7):

    logs_path = r'logs'
    os.path.isdir(logs_path)
    report = {}
    report['start'] = dt.date.today() - dt.timedelta(days = days)
    report['end'] = dt.date.today()
    report['sum_of_errors'] = 0
    report['sum_of_warnings'] = 0

    for file in os.listdir(logs_path):
        date = dt.date(int(file.split('-')[0]), int(file.split('-')[1]), int(file.split('-')[2].split(".")[0]))
        if date  > dt.date.today() - dt.timedelta(days = days):
            day = {}
            day['date'] = date
            day['errors'] = 0
            day['warnings'] = 0

            with open(os.path.join(logs_path, file), 'r') as log:
                for line in log:
                    if line[0] == '[' and line.rstrip("\n").split(" ")[2] == "ERROR":
                        day['errors'] +=1
                    if line[0] == '[' and line.rstrip("\n").split(" ")[2] == "WARNING":
                        day['warnings'] +=1

            report['sum_of_errors'] += day['errors']
            report['sum_of_warnings'] += day['warnings']
            report[file.split('-')[0] + file.split('-')[1] + file.split('-')[2].split(".")[0]] = day

    return report

class StatisticalSummary():

    def __init__(self, number_of_days) -> None:

        from user.classes import User
        from activity.classes import Activities
        from event.classes import Event

        self.days = number_of_days
        self.start_date = dt.date.today() - dt.timedelta(days=number_of_days)
        self.end_date = dt.date.today() - dt.timedelta(days=1)
        self.new_activities = Activities.added_in_last_days(self.days)
        self.new_users = User.added_in_last_days(self.days)
        self.new_events = Event.added_in_last_days(self.days)
        
        report = generate_error_summary(self.days)
        self.errors = report['sum_of_errors']
        self.warnings = report['sum_of_warnings']


            

