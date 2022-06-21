from start import db
from flask_login import current_user
from flask import render_template, current_app, request, flash
from flask_mail import Mail, Message
from start import app
from user.classes import User
from other.classes import mailboxMessage
from event.classes import Event
import datetime

mail = Mail(app)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject, recipients=[to])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    mail.send(msg)
    return None


def prepareListOfChoices():

    allUsers = [('Wszyscy','Wszyscy')]
    availableListOfUsers = prepareListOfUsers()
    availableListOfEvents = crateAvailableListOfEvents()
   
    availableListOfChoices = allUsers + availableListOfEvents + availableListOfUsers
    return availableListOfChoices


def prepareListOfUsers():
    #Creating list of users
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
    return list(zip(listOfUsersMails, listOfUsersFullNames))


def crateAvailableListOfEvents():
    # Creating list of events
    listOfEvents=Event.query.all()
    listOfEventsNameKey = []
    listOfEventsNameValue = []

    for event in listOfEvents:
        key = event.name + ", ID:" + str(event.id)
        value = "Uczestnicy wyzwania: " + event.name
        listOfEventsNameKey.append(key)
        listOfEventsNameValue.append(value)

    return list(zip(listOfEventsNameKey, listOfEventsNameValue))


def saveMessageInDB(form):
    
    senderFullName=setSenderFullName()
    receiverFullName=setReceiverFullName(form)

    newMessage = mailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=False )
    db.session.add(newMessage)
    db.session.commit()
    newMessage = mailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=True )
    db.session.add(newMessage)
    db.session.commit()


def setSenderFullName():
    senderName=current_user.name
    senderLastName=current_user.lastName
    return senderName + " " + senderLastName

def setReceiverFullName(form):
    receiverUser=User.query.filter(User.mail==form.receiverEmail.data).first()
    receiverName=receiverUser.name
    receiverLastName=receiverUser.lastName
    return receiverName + " " + receiverLastName


def saveMessageInDBforEvent(form):
    senderFullName=setSenderFullName()
    (eventName, id) = (form.receiverEmail.data).split(', ID:')
    newMessage = mailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = eventName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=False )
    db.session.add(newMessage)
    db.session.commit()

    event=Event.query.filter(Event.name==eventName).first()
    for participant in event.participants:
        receiverUser=User.query.filter(User.id==participant.user_name).first()
        receiverMail=receiverUser.mail
        receiverName=receiverUser.name
        receiverLastName=receiverUser.lastName
        receiverFullName=receiverName + " " + receiverLastName
        newMessage = mailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = receiverMail, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=True )
        db.session.add(newMessage)
        db.session.commit()


def saveMessageInDBforAll(form):
    senderFullName=setSenderFullName()
    newMessage = mailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = form.receiverEmail.data, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=False )
    db.session.add(newMessage)
    db.session.commit()

    users=User.query.all()
    for user in users:
        receiverMail=user.mail
        receiverName=user.name
        receiverLastName=user.lastName
        receiverFullName=receiverName + " " + receiverLastName
        newMessage = mailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = receiverMail, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=True )
        db.session.add(newMessage)
        db.session.commit()

    
def deleteMessagesFromDB(messagesToDelete):

    for messageID in messagesToDelete:
        messageToDelete=mailboxMessage.query.filter(mailboxMessage.id == messageID).first()
        db.session.delete(messageToDelete)
        db.session.commit()
    return None
    
@app.context_processor
def cookies_check():
    value = request.cookies.get('cookie_consent')
    return dict(cookies_check = value == 'true')

