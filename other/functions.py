import imp
from start import db
from flask_login import current_user
from flask import render_template, current_app, request, flash, redirect, url_for
from flask_mail import Mail, Message
from start import app
# from user.classes import User
from .classes import MailboxMessage
from event.classes import Event
import datetime

mail = Mail(app)

def send_email(to, subject, template, **kwargs):
    try:
        app = current_app._get_current_object()
        msg = Message(subject, recipients=[to])
        msg.body = render_template(template + ".txt", **kwargs)
        msg.html = render_template(template + ".html", **kwargs)
        mail.send(msg)
        current_app.logger.info(f"Mail sent to: {to}. Subject: {subject}.")
        return None

    except:
        current_app.logger.exception(f"Failed to sent mail to: {to}. Subject: {subject}.")



def prepareListOfChoicesForAdmin():

    allUsers = [('Wszyscy','Wszyscy')]
    availableListOfUsers = prepareListOfUsers()
    availableListOfEvents = crateAvailableListOfEvents()
   
    availableListOfChoices = allUsers + availableListOfEvents + availableListOfUsers
    return availableListOfChoices

def prepareListOfChoicesForNormalUser():

    adminUser=prepareListOfAdmins()
    currentUserEventsUsers=prepareListOfCurrentUserEventsUsers()
    currentUserEventsSingleUsers=prepareListOfCurrentUserEventsSingleUsers()
    availableListOfChoices=adminUser+currentUserEventsUsers+currentUserEventsSingleUsers
    return availableListOfChoices


def prepareListOfUsers():
    #Creating list of users

    from user.classes import User

    listOfUsers=User.query.all()
    listOfUsersMails = [(a.mail) for a in listOfUsers]
    listOfUsersNames = [(a.name) for a in listOfUsers]
    listOfUsersLastNames = [(a.last_name) for a in listOfUsers]

    tempTupleNameList=list(zip(listOfUsersNames,listOfUsersLastNames))
    listOfUsersFullNames = []

    for name, last_name in tempTupleNameList:
        fullName=name+" "+last_name
        listOfUsersFullNames.append(fullName)

    # (mails, name & last name) 
    return list(zip(listOfUsersMails, listOfUsersFullNames))

def prepareListOfAdmins():

    from user.classes import User
    
    listOfAdmins=User.query.filter(User.isAdmin==True).all()

    listOfAdminsMails = [(a.mail) for a in listOfAdmins]
    listOfAdminsNames = [(a.name) for a in listOfAdmins]
    listOfAdminsLastNames = [(a.lastName) for a in listOfAdmins]

    tempTupleNameList=list(zip(listOfAdminsNames,listOfAdminsLastNames))
    listOfAdminsFullNames = []

    for name, lastName in tempTupleNameList:
        fullName=name+" "+lastName
        listOfAdminsFullNames.append(fullName)

    return list(zip(listOfAdminsMails, listOfAdminsFullNames))

def prepareListOfCurrentUserEventsUsers():
    listOfEvents=Event.query.all()
    listOfRealEvents=[]

    for event in listOfEvents:
        for participant in event.participants:
            if participant.user_name==current_user.id:
                listOfRealEvents.append(event.name)
                break

    listOfEventsNameKey = []
    listOfEventsNameValue = []

    for event in listOfRealEvents:
        singleEvent=Event.query.filter(Event.name==event).first()
        key = singleEvent.name + ", ID:" + str(singleEvent.id)
        value = "Uczestnicy wyzwania: " + singleEvent.name
        listOfEventsNameKey.append(key)
        listOfEventsNameValue.append(value)
    
    return list(zip(listOfEventsNameKey, listOfEventsNameValue))

def prepareListOfCurrentUserEventsSingleUsers():

    from user.classes import User

    listOfEvents=Event.query.all()
    listOfRealEvents=[]

    for event in listOfEvents:
        for participant in event.participants:
            if participant.user_name==current_user.id:
                listOfRealEvents.append(event.name)
                break

    listOfAdmins=prepareListOfAdmins()
    listOfMails = []
    listOfFullNames = []


    try:

        for singleEvent in listOfRealEvents:
            event=Event.query.filter(Event.name==singleEvent).first()
            for participant in event.participants:
                receiverUser=User.query.filter(User.id==participant.user_name).first()
                receiverMail=receiverUser.mail
                receiverName=receiverUser.name
                receiverLastName=receiverUser.lastName
                receiverFullName=receiverName + " " + receiverLastName
                if receiverMail is not current_user.mail and not receiverMail in listOfMails and not receiverMail in listOfAdmins[0] and not receiverMail in listOfAdmins[1] and not receiverMail in listOfAdmins[3]:
                    listOfMails.append(receiverMail)
                    listOfFullNames.append(receiverFullName)
                

    except:
        current_app.logger.exception(f"Somethink went wrong!")
         
    return list(zip(listOfMails, listOfFullNames))

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
    try:
        senderFullName=setSenderFullName()
        receiverFullName=setReceiverFullName(form)

        newMessage = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=False )
        db.session.add(newMessage)
        db.session.commit()
        newMessage = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=True )
        db.session.add(newMessage)
        db.session.commit()
        app.logger.info(f"User {current_user.id} sent message to {receiverFullName}.")
    except:
        current_app.logger.exception(f"User {current_user.id} failed to send message to {receiverFullName}.")

def setSenderFullName():
    senderName=current_user.name
    senderLastName=current_user.last_name
    return senderName + " " + senderLastName

def setReceiverFullName(form):

    from user.classes import User

    receiverUser=User.query.filter(User.mail==form.receiverEmail.data).first()
    receiverName=receiverUser.name
    receiverLastName=receiverUser.last_name
    return receiverName + " " + receiverLastName


def saveMessageInDBforEvent(form):

    from user.classes import User

    try:
        senderFullName=setSenderFullName()
        (eventName, id) = (form.receiverEmail.data).split(', ID:')
        newMessage = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = eventName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=False )
        db.session.add(newMessage)
        db.session.commit()

        event=Event.query.filter(Event.name==eventName).first()
        for participant in event.participants:
            receiverUser=User.query.filter(User.id==participant.user_name).first()
            receiverMail=receiverUser.mail
            receiverName=receiverUser.name
            receiverLastName=receiverUser.lastName
            receiverFullName=receiverName + " " + receiverLastName
            newMessage = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = receiverMail, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=True )
            db.session.add(newMessage)
            db.session.commit()
            app.logger.info(f"User {current_user.id} sent message to {eventName} participants.")
    except:
        current_app.logger.exception(f"User {current_user.id} failed to send message to {eventName} participants.")

def saveMessageInDBforAll(form):

    from user.classes import User
    try:
        senderFullName=setSenderFullName()
        newMessage = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = form.receiverEmail.data, receiverName = form.receiverEmail.data, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=False )
        db.session.add(newMessage)
        db.session.commit()

        users=User.query.all()
        for user in users:
            receiverMail=user.mail
            receiverName=user.name
            receiverLastName=user.lastName
            receiverFullName=receiverName + " " + receiverLastName
            newMessage = MailboxMessage(date=datetime.date.today(), sender=current_user.mail, senderName=senderFullName, receiver = receiverMail, receiverName = receiverFullName, subject = form.subject.data, message = form.message.data, sendByApp = form.sendByApp.data, sendByEmail= form.sendByEmail.data, messageReaded=False, multipleMessage=True )
            db.session.add(newMessage)
            db.session.commit()

        app.logger.info(f"User {current_user.id} sent message to all users.")
    except:
        current_app.logger.exception(f"User {current_user.id} failed to send message to all users.")

def sendMessgaeFromContactFormToDB(newMessage):
    try:
        db.session.add(newMessage)
        db.session.commit()
        app.logger.info(f"Message sent from contact form.")
    except:
        current_app.logger.exception(f"User failed to send message from contact form.")

    
def deleteMessagesFromDB(messagesToDelete):
    try:
        for messageID in messagesToDelete:
            messageToDelete=MailboxMessage.query.filter(MailboxMessage.id == messageID).first()
            db.session.delete(messageToDelete)
            db.session.commit()
        return None
    except:
         current_app.logger.exception(f"User failed to delete message from mailbox.")
    
    
@app.context_processor
def cookies_check():
    value = request.cookies.get('cookie_consent')
    return dict(cookies_check = value == 'true')



# def account_confirmation_check(initial_function):

#     def wrapped_function(*args, **kwargs):

#         if current_user.is_authenticated and not current_user.confirmed:
#             return redirect(url_for('user.unconfirmed'))


#         else:
#             wrapped_route = initial_function(*args, **kwargs)
#             return wrapped_function
        
#     return wrapped_function