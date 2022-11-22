from flask_login import current_user, login_required
from flask import Blueprint, make_response, render_template, redirect, url_for, blueprints, request

from flask import flash

from datetime import datetime, timedelta
import datetime

from .classes import MailboxMessage
from .forms import MessageForm,  AppMailForm, AppMailToRead
from .functions import send_email, prepareListOfChoicesForAdmin, saveMessageInDB, deleteMessagesFromDB, saveMessageInDBforEvent, saveMessageInDBforAll, prepareListOfChoicesForNormalUser, sendMessgaeFromContactFormToDB
from user.classes import User
from user.functions import account_confirmation_check

from start import db    

other = Blueprint("other", __name__,
    template_folder='templates')

@other.route("/")
def hello():

    print(current_user)

    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    return render_template("pages/index.html", title_prefix = "Home")

@other.route("/faq")
def faq():

    return render_template('/pages/faq.html', title_prefix = "FAQ" )

@other.route("/about")
def about():

    return render_template('/pages/about.html', title_prefix = "O nas" )


@other.route("/sendMessage", methods=['POST','GET'])
def sendMessage():

    if current_user.is_authenticated:
        form=MessageForm(name=current_user.name, lastName=current_user.lastName, mail=current_user.mail)
        form.name.data = form.name.data+" "+form.lastName.data
    else:
        form=MessageForm()
        form.lastName.data="-"


    if form.validate_on_submit():


        if current_user.is_authenticated:
            send_email("admin@sportoweswiry.atthost24.pl", "Wiadomość od użytkownika {} {} - {}".format(current_user.name, current_user.lastName, form.subject.data),'message', 
                        name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, message=form.message.data)
        else:
            send_email("admin@sportoweswiry.atthost24.pl", "Wiadomość od użytkownika {} {} - {}".format(form.name.data, form.lastName.data, form.subject.data),'message', 
                        name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, message=form.message.data)

        admins = User.query.filter(User.isAdmin==True).all()
        for admin in admins:
            if current_user.is_authenticated:
                newMessage = MailboxMessage(date=datetime.date.today(), sender=form.mail.data, senderName=current_user.name+" "+current_user.lastName, receiver = admin.mail, receiverName = admin.name+" "+admin.lastName, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, sendByApp = False, sendByEmail= True, messageReaded=False, multipleMessage=True)
            else:
                newMessage = MailboxMessage(date=datetime.date.today(), sender=form.mail.data, senderName=form.name.data, receiver = admin.mail, receiverName = admin.name+" "+admin.lastName, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, sendByApp = False, sendByEmail= True, messageReaded=False, multipleMessage=True)
            sendMessgaeFromContactFormToDB(newMessage)
        
        flash("Wiadomość została wysłana. Odpowiemy najszybciej jak to możliwe.")
        return redirect(url_for('other.contactFormResponse'))

    return render_template('/pages/sendMessage.html', form=form, title_prefix = "Formularz kontaktowy" )

@other.route("/mailbox/<actionName>", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def mailbox(actionName):

    form=AppMailForm()
    readForm=AppMailToRead()

    if current_user.is_admin == True:
        form.receiverEmail.choices = prepareListOfChoicesForAdmin()
    else:
        form.receiverEmail.choices = prepareListOfChoicesForNormalUser()

    if form.validate_on_submit():

        if form.receiverEmail.data=="Wszyscy":
            saveMessageInDBforAll(form)
            flash("Wiadomość przesłana do wszystkich użytkowników aplikacji")
        elif ("ID:" in form.receiverEmail.data):
            saveMessageInDBforEvent(form)
            (eventName, id) = (form.receiverEmail.data).split(', ID:')
            flash("Wiadomość przesłana do uczestników wyzwania: {}".format(eventName))
        else:
            saveMessageInDB(form)
            flash("Wiadomość przesłana do użytkownika: {}".format(form.receiverEmail.data))

    elif request.method == 'POST':
        messagesToDelete=request.form.getlist('checkboxesWithMessagesToDelete')
        if not messagesToDelete:
            flash("Brak zaznaczonych wiadomości do usunięcia")
        else:
            deleteMessagesFromDB(messagesToDelete)
            flash ("Zaznaczone wiadomości zostały poprawnie usnięte")
        return redirect(url_for('other.mailbox', actionName='inbox'))



    messagesCurrentUserReceived = MailboxMessage.query.filter(MailboxMessage.receiver == current_user.mail).filter(MailboxMessage.multipleMessage == True).order_by(MailboxMessage.id.desc()).all()
 
    print(messagesCurrentUserReceived)
    messagesCurrentUserSent = MailboxMessage.query.filter(MailboxMessage.sender == current_user.mail).filter(MailboxMessage.multipleMessage == False).order_by(MailboxMessage.id.desc()).all()
    print(messagesCurrentUserSent)
    amountOfReceivedMessages=len(messagesCurrentUserReceived)
    amountOfSentMessages=len(messagesCurrentUserSent)

    if actionName=='sent':
        messagesCurrentUser=messagesCurrentUserSent
    else:
        messagesCurrentUser=messagesCurrentUserReceived


    return render_template('/pages/mailbox.html', form=form, readForm=readForm, messagesCurrentUser=messagesCurrentUser, current_user=current_user, 
            amountOfReceivedMessages=amountOfReceivedMessages, amountOfSentMessages=amountOfSentMessages, actionName=actionName, menuMode="mainApp")

@other.route("/acceptCookies", methods=['POST','GET'])
def acceptCookies():

    if request.method == 'POST':

        expire_date = datetime.datetime.now() + datetime.timedelta(days=365)
        response = make_response(redirect(url_for('other.hello')))
        response.set_cookie(key='cookie_consent', value='true', expires=expire_date)

        return response
    
    return redirect(url_for('other.hello'))

@other.route("/privacyPolicy")
def privacyPolicy():
    
    return render_template('/pages/privacyPolicy.html', title_prefix= "Polityka Prywatności")

@other.route("/contactFormResponse")
def contactFormResponse():

    return render_template('/pages/messageSent.html', title_prefix = "Formularz kontaktowy" )

@other.route("/changeMessageStatus/<messageID>", methods=['POST','GET'])
def changeStatusOfMessage(messageID):
    current_user.changeStatusOfMessage(messageID)
    return redirect(url_for('other.mailbox', actionName='inbox'))


import csv

@other.route('/copy_data')
def copy_data():

    #copy_messages_from_csv("mailbox_message.csv")
    #copy_users_from_csv('user.csv')
    # copy_events_from_csv('event.csv')
    # copy_coefficients_from_csv("coefficients_list.csv")
    # copy_distances_from_csv("distances_table.csv")
    # copy_participation_from_csv("participation.csv")
    

    # copy_activities_from_csv('activities.csv')

    return redirect(url_for('other.hello'))


@other.route('/copy_messages')
def copy_messages():
    
    copy_messages_from_csv("mailbox_message.csv")

    return redirect(url_for('other.hello'))


def copy_messages_from_csv(file_path):

    with open(file_path, encoding="utf8") as messages_file:
        a = csv.DictReader(messages_file)
        for row in a:

            if row["sendByApp"] == 'NULL' or row["sendByApp"] == '0':
                row["sendByApp"] = False
            else:
                row["sendByApp"] = True

            if row["sendByEmail"] == 'NULL' or row["sendByEmail"] == '0':
                row["sendByEmail"] = False
            else:
                row["sendByEmail"] = True

            if row["messageReaded"] == 'NULL' or row["messageReaded"] == '0':
                row["messageReaded"] = False
            else:
                row["messageReaded"] = True


            if row["multipleMessage"] == 'NULL' or row["multipleMessage"] == '0':
                row["multipleMessage"] = False
            else:
                row["multipleMessage"] = True

            sender = User.query.filter(User.mail == row['sender']).first()
            reciver = User.query.filter(User.mail == row['receiver']).first()
            
            if row['receiver'] != "Wszyscy":

                new_message = MailboxMessage(id = row["id"], date = row["date"], sender = sender.id, receiver = reciver.id, 
                subject = row["subject"], message = row["message"], send_by_app = row["sendByApp"], send_by_email = row["sendByEmail"],
                message_readed = row["messageReaded"], multiple_message = row['multipleMessage'] )

                try:
                    db.session.add(new_message)
                    db.session.commit()

                except:
                    print('Error', row['id'])

    return True