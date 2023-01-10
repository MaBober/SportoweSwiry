
from start import db, app
from flask import render_template, current_app, request
from flask_mail import Mail, Message


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


def send_message_from_contact_form_to_db(new_message):
    try:
        db.session.add(new_message)
        db.session.commit()
        app.logger.info(f"Message sent from contact form.")
    except:
        current_app.logger.exception(f"User failed to send message from contact form.")

    
    
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