
from start import db
from flask_login import current_user
from flask import render_template, current_app
from flask_mail import Mail, Message
from start import app
from user.classes import User
from other.classes import mailboxMessage
import datetime

mail = Mail(app)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject, recipients=[to])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    mail.send(msg)
    return None


def prepareListOfUsers():
    # Creating list of users
    listOfUsers=User.query.all()
    listOfUsersMails = [(a.mail) for a in listOfUsers]
    listOfUsersNames = [(a.name) for a in listOfUsers]
    listOfUsersLastNames = [(a.lastName) for a in listOfUsers]

    tempTupleNameList=list(zip(listOfUsersNames,listOfUsersLastNames))
    listOfUsersFullNames = []

    for name, lastName in tempTupleNameList:
        fullName=name+" "+lastName
        listOfUsersFullNames.append(fullName)

    # (mails, name & last name) 
    availableListOfUsers = list(zip(listOfUsersMails, listOfUsersFullNames))
    return availableListOfUsers

def saveMessageInDB(form):
    newMessage = mailboxMessage(date=datetime.date.today(), sender=current_user.mail, receiver = form.receiverEmail.data, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data )
    db.session.add(newMessage)
    db.session.commit()