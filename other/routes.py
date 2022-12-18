from flask_login import current_user, login_required
from flask import Blueprint, make_response, render_template, redirect, url_for, blueprints, request

from flask import flash

from datetime import datetime, timedelta
import datetime

from .classes import MailboxMessage
from .forms import MessageForm,  AppMailForm, AppMailToRead
from .functions import send_email, prepare_list_of_choices_for_admin, save_message_in_db, delete_messages_from_db, save_message_in_db_for_event, save_message_in_db_for_all, prepare_list_of_choices_for_normal_user, send_message_from_contact_form_to_db
from user.classes import User
from user.functions import account_confirmation_check

from start import db    

other = Blueprint("other", __name__,
    template_folder = 'templates',
    static_folder = 'static',
    static_url_path = '/other/static')

@other.route("/")
def hello():

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


@other.route("/send_message", methods=['POST','GET'])
def send_message():

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
                new_message = MailboxMessage(date=datetime.date.today(), sender=form.mail.data, senderName=current_user.name+" "+current_user.last_name, receiver = admin.mail, receiverName = admin.name+" "+admin.last_name, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, sendByApp = False, sendByEmail= True, messageReaded=False, multiple_message=True)
            else:
                new_message = MailboxMessage(date=datetime.date.today(), sender=form.mail.data, senderName=form.name.data, receiver = admin.mail, receiverName = admin.name+" "+admin.last_name, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, sendByApp = False, sendByEmail= True, messageReaded=False, multiple_message=True)
            send_message_from_contact_form_to_db(new_message)
        
        flash("Wiadomość została wysłana. Odpowiemy najszybciej jak to możliwe.")
        return redirect(url_for('other.contact_form_response'))

    return render_template('/pages/send_message.html', form=form, title_prefix = "Formularz kontaktowy" )

@other.route("/mailbox/<actionName>", methods=['POST','GET'])
@account_confirmation_check
@login_required #This page needs to be login
def mailbox(actionName):

    form=AppMailForm()
    read_form=AppMailToRead()

    if current_user.is_admin == True:
        form.receiver_email.choices = prepare_list_of_choices_for_admin()
    else:
        form.receiver_email.choices = prepare_list_of_choices_for_normal_user()

    if form.validate_on_submit():

        if form.receiver_email.data=="Wszyscy":
            save_message_in_db_for_all(form)
            flash("Wiadomość przesłana do wszystkich użytkowników aplikacji")
        elif ("ID:" in form.receiver_email.data):
            save_message_in_db_for_event(form)
            (event_name, id) = (form.receiver_email.data).split(', ID:')
            flash("Wiadomość przesłana do uczestników wyzwania: {}".format(event_name))
        else:
            save_message_in_db(form)
            flash("Wiadomość przesłana do użytkownika: {}".format(form.receiver_email.data))

    elif request.method == 'POST':
        messages_to_delete=request.form.getlist('checkboxesWithMessagesToDelete')
        if not messages_to_delete:
            flash("Brak zaznaczonych wiadomości do usunięcia")
        else:
            delete_messages_from_db(messages_to_delete)
            flash ("Zaznaczone wiadomości zostały poprawnie usnięte")
        return redirect(url_for('other.mailbox', actionName='inbox'))



    messages_current_user_received = MailboxMessage.query.filter(MailboxMessage.receiver == current_user.mail).filter(MailboxMessage.multiple_message == True).order_by(MailboxMessage.id.desc()).all()
    messages_current_user_sent = MailboxMessage.query.filter(MailboxMessage.sender == current_user.mail).filter(MailboxMessage.multiple_message == False).order_by(MailboxMessage.id.desc()).all()

    amount_of_received_messages=len(messages_current_user_received)
    amount_of_sent_messages=len(messages_current_user_sent)

    if actionName=='sent':
        messages_current_user=messages_current_user_sent
    else:
        messages_current_user=messages_current_user_received


    return render_template('/pages/mailbox.html', form=form, readForm=read_form, messages_current_user=messages_current_user, current_user=current_user, 
            amount_of_received_messages=amount_of_received_messages, amount_of_sent_messages=amount_of_sent_messages, actionName=actionName, menuMode="mainApp")

@other.route("/accept_cookies", methods=['POST','GET'])
def accept_cookies():

    if request.method == 'POST':

        expire_date = datetime.datetime.now() + datetime.timedelta(days=365)
        response = make_response(redirect(url_for('other.hello')))
        response.set_cookie(key='cookie_consent', value='true', expires=expire_date)

        return response
    
    return redirect(url_for('other.hello'))

@other.route("/privacy_policy")
def privacy_policy():
    
    return render_template('/pages/privacy_policy.html', title_prefix= "Polityka Prywatności")

@other.route("/contact_form_response")
def contact_form_response():

    return render_template('/pages/message_sent.html', title_prefix = "Formularz kontaktowy" )

@other.route("/change_message_status/<messageID>", methods=['POST','GET'])
def change_message_status(message_id):
    current_user.change_message_status(message_id)
    return redirect(url_for('other.mailbox', actionName='inbox'))

