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


@other.route("/regulamin")
def statute():
    
    return render_template('/pages/statute.html', title_prefix = "Regulamin" )

@other.route("/about")
def about():

    return render_template('/pages/about.html', title_prefix = "O nas" )


@other.route("/sendMessage", methods=['POST','GET'])
def sendMessage():

    if current_user.is_authenticated:
        form=MessageForm(name=current_user.name, lastName=current_user.last_name, mail=current_user.mail)
        form.name.data = form.name.data+" "+form.lastName.data
    else:
        form=MessageForm()
        form.lastName.data="-"


    if form.validate_on_submit():

        if current_user.is_authenticated:
            send_email("admin@sportoweswiry.atthost24.pl", "Wiadomość od użytkownika {} {} - {}".format(current_user.name, current_user.last_name, form.subject.data),'message', 
                        name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, message=form.message.data)
        else:
            send_email("admin@sportoweswiry.atthost24.pl", "Wiadomość od użytkownika {} {} - {}".format(form.name.data, form.lastName.data, form.subject.data),'message', 
                        name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, message=form.message.data)

        admins = User.query.filter(User.is_admin == True).all()
        for admin in admins:
            if current_user.is_authenticated:
                newMessage = MailboxMessage(date=datetime.date.today(), sender=form.mail.data, senderName=current_user.name+" "+current_user.last_name, receiver = admin.mail, receiverName = admin.name+" "+admin.last_name, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, sendByApp = False, sendByEmail= True, messageReaded=False, multipleMessage=True)
            else:
                newMessage = MailboxMessage(date=datetime.date.today(), sender=form.mail.data, senderName=form.name.data, receiver = admin.mail, receiverName = admin.name+" "+admin.last_name, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, sendByApp = False, sendByEmail= True, messageReaded=False, multipleMessage=True)
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

