
from random import choices
from flask_login import current_user, login_required
from flask import Blueprint, make_response, render_template, redirect, url_for, blueprints, request

from flask import flash
from .forms import MessageForm,  AppMailForm, AppMailToRead
from user.classes import User

from other.classes import mailboxMessage
from .functions import send_email, prepareListOfUsers, saveMessageInDB
from datetime import datetime, timedelta


other = Blueprint("other", __name__,
    template_folder='templates')


@other.route("/")
def hello():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    if current_user.is_authenticated:
        return redirect(url_for('user.basicDashboard'))

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
    else:
        form=MessageForm()

    if form.validate_on_submit():

        # admins=User.query.filter(User.isAdmin == True).all()

        # for admin in admins:
        send_email("admin@sportoweswiry.atthost24.pl", "Wiadomość od użytkownika {} {} - {}".format(form.name.data, form.lastName.data, form.subject.data),'message', 
                        name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, message=form.message.data)

        
        flash("Wiadomość została wysłana. Odpowiemy najszybciej jak to możliwe.")
        return render_template('/pages/messageSent.html', title_prefix = "Formularz kontaktowy" )

    return render_template('/pages/sendMessage.html', form=form, title_prefix = "Formularz kontaktowy" )

@other.route("/mailbox/<actionName>", methods=['POST','GET'])
@login_required #This page needs to be login
def mailbox(actionName):

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('user.unconfirmed'))

    form=AppMailForm()
    readForm=AppMailToRead()

    form.receiverEmail.choices = prepareListOfUsers()

    if form.validate_on_submit():

        saveMessageInDB(form)
        flash("Wiadomość przesłana do: {}".format(form.receiverEmail.data))


    messagesCurrentUserReceived=mailboxMessage.query.filter(mailboxMessage.receiver == current_user.mail).order_by(mailboxMessage.id.desc()).all()
    messagesCurrentUserSent=mailboxMessage.query.filter(mailboxMessage.sender == current_user.mail).order_by(mailboxMessage.id.desc()).all()
    amountOfReceivedMessages=len(messagesCurrentUserReceived)
    amountOfSentMessages=len(messagesCurrentUserSent)

    if actionName=='sent':
        messagesCurrentUser=messagesCurrentUserSent
    else:
        messagesCurrentUser=messagesCurrentUserReceived


    return render_template('/pages/mailbox.html', form=form, readForm=readForm, messagesCurrentUser=messagesCurrentUser, current_user=current_user, 
            amountOfReceivedMessages=amountOfReceivedMessages, amountOfSentMessages=amountOfSentMessages, actionName=actionName)

@other.route("/acceptCookies", methods=['POST','GET'])
def acceptCookies():

    if request.method == 'POST':

        expire_date = datetime.now() + timedelta(days=365)
        response = make_response(redirect(url_for('other.hello')))
        response.set_cookie(key='cookie_consent', value='true', expires=expire_date)

        return response
    
    return redirect(url_for('other.hello'))

@other.route("/privacyPolicy")
def privacyPolicy():

    return render_template('/pages/privacyPolicy.html', title_prefix= "Polityka Prywatności")



@other.route("/test", methods=['POST', 'GET'])
def test():

    form=MessageForm()
    return render_template("/pages/messageSent.html", form=form)
