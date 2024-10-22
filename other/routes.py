from flask_login import current_user, login_required
from flask import Blueprint, make_response, render_template, redirect, url_for, request, flash

from .classes import MailboxMessage
from .forms import MessageForm,  AppMailForm, AppMailToRead
from .functions import send_email, send_message_from_contact_form_to_db
from user.classes import User
from user.functions import account_confirmation_check

import datetime as dt
  

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

    from activity.classes import Sport

    all_sports = Sport.all_sports()

    return render_template('/pages/faq.html', title_prefix = "FAQ", all_sports = all_sports )


@other.route("/regulamin")
def statute():
    
    return render_template('/pages/statute.html', title_prefix = "Regulamin" )

@other.route("/about")
def about():

    return render_template('/pages/about.html', title_prefix = "O nas" )


@other.route("/historia")
def history():

    return render_template('/pages/history.html', title_prefix = "Jak to się zaczęło?" )

@other.route("/jak_to_dziala")
def how_it_works():

    return render_template('/pages/how_it_works.html', title_prefix = "Jakt to działa?" ) 

@other.route("/instrukcja")
def instruction():

    return render_template('/pages/instruction.html', title_prefix = "Instrukcja" ) 

@other.route("/krypto_tip")
def crypto_tip():

    return render_template('/pages/crypto_tip.html', title_prefix = "Napiwek w kryptowalutach" ) 

@other.route("/admin_panel")
@account_confirmation_check
def admin_panel():

    if not current_user.is_admin:
        flash("Nie masz uprawnień do tej zawartości")
        return redirect(url_for('other.hello'))

    from user.classes import User
    from activity.classes import Activities
    from event.classes import Event

    ranges = [1,7,30]
    data = {'users' : [],
            'events' : [],
            'activities' : []
            }

    for range in ranges:
        data['activities'].append(Activities.added_in_last_days(range))
        data['users'].append(User.added_in_last_days(range))
        data['events'].append(Event.added_in_last_days(range))


    return render_template('/pages/admin_panel.html', title_prefix = "Panel Administratora", menu_mode = "mainApp", data = data )


@other.route("/send_message", methods=['POST','GET'])
def send_message():

    if current_user.is_authenticated:
        if 'sport_proposal' in request.args and request.args['sport_proposal'] == 'True':
            form = MessageForm(name = current_user.name,
                                last_name =  current_user.last_name,
                                mail = current_user.mail,
                                subject = "Propozycja dodania nowego sportu",
                                message = 'Cześć,\nProponuję dodać do aplikacji sport : [PODAJ NAZWĘ SPORTU],\nze [STAŁĄ/WSPÓŁCZYNNIKIEM] o wartości [PODAJ PROPONOWANĄ WARTOŚĆ].')
            form.name.data = form.name.data + " " + form.last_name.data
        else:
            form=MessageForm(name = current_user.name,
                             last_name = current_user.last_name,
                             mail=current_user.mail)
            form.name.data = form.name.data + " " + form.last_name.data
    else:
        form=MessageForm()
        form.last_name.data="-"


    if form.validate_on_submit():

        if current_user.is_authenticated:
            send_email("kontakt@sportoweswiry.com.pl", "Wiadomość od użytkownika {} {} - {}".format(current_user.name, current_user.last_name, form.subject.data),'message', 
                        name=form.name.data, last_name=form.last_name.data, mail=form.mail.data, message=form.message.data, topic = form.subject.data)
        else:
            send_email("kontakt@sportoweswiry.com.pl", "Wiadomość od użytkownika {} {} - {}".format(form.name.data, form.last_name.data, form.subject.data),'message', 
                        name=form.name.data, last_name=form.last_name.data, mail=form.mail.data, message=form.message.data, topic = form.subject.data)

        admins = User.query.filter(User.is_admin == True).all()
        for admin in admins:
            if current_user.is_authenticated:
                new_message = MailboxMessage(date = dt.date.today(), sender=form.mail.data, sender_name=current_user.name+" "+current_user.last_name, receiver = admin.mail, receiver_name = admin.name+" "+admin.last_name, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, send_by_app = False, send_by_email= True, message_readed=False, multiple_message=True)
            else:
                new_message = MailboxMessage(date = dt.date.today(), sender=form.mail.data, sender_name=form.name.data, receiver = admin.mail, receiver_name = admin.name+" "+admin.last_name, subject = "Formularz kontaktowy: "+form.subject.data, message = form.message.data, send_by_app = False, send_by_email= True, message_readed=False, multiple_message=True)
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
        form.receiver_email.choices = MailboxMessage.prepare_list_of_choices_for_admin()
    else:
        form.receiver_email.choices = MailboxMessage.prepare_list_of_choices_for_normal_user()

    if form.validate_on_submit():

        if form.receiver_email.data=="Wszyscy":
            MailboxMessage.save_message_in_db_for_all(form)
            flash("Wiadomość przesłana do wszystkich użytkowników aplikacji")
        elif ("ID:" in form.receiver_email.data):
            MailboxMessage.save_message_in_db_for_event(form)
            (event_name, id) = (form.receiver_email.data).split(', ID:')
            flash("Wiadomość przesłana do uczestników wyzwania: {}".format(event_name))
        else:
            MailboxMessage.save_message_in_db(form)
            receiver_full_name=MailboxMessage.set_receiver_full_name(form)
            flash("Wiadomość przesłana do użytkownika: {}".format(receiver_full_name))

    elif request.method == 'POST':
        messages_to_delete=request.form.getlist('checkboxesWithMessagesToDelete')
        if not messages_to_delete:
            flash("Brak zaznaczonych wiadomości do usunięcia")
        else:
            MailboxMessage.delete_messages_from_db(messages_to_delete)
            flash ("Zaznaczone wiadomości zostały poprawnie usunięte")
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
            amount_of_received_messages=amount_of_received_messages, amount_of_sent_messages=amount_of_sent_messages, actionName=actionName, menu_mode="mainApp")

@other.route("/accept_cookies", methods=['POST','GET'])
def accept_cookies():

    
    if 'source' in request.args:
        source = request.args['source']
    
    else:
        source = url_for('other.hello')

    if request.method == 'POST':

        expire_date = dt.datetime.now() + dt.timedelta(days=365)
        response = make_response(redirect(source))
        response.set_cookie(key='cookie_consent', value='true', expires=expire_date)

        return response
    
    return redirect(source)

@other.route("/polityka_prywatnosci")
def privacy_policy():
    
    return render_template('/pages/privacy_policy.html', title_prefix= "Polityka Prywatności")

@other.route("/contact_form_response")
def contact_form_response():

    return render_template('/pages/message_sent.html', title_prefix = "Formularz kontaktowy" )

@other.route("/change_message_status/<message_id>", methods=['POST','GET'])
def change_message_status(message_id):
    current_user.change_message_status(message_id)
    return redirect(url_for('other.mailbox', actionName='inbox'))

