from flask import render_template, current_app, request, flash
from flask_mail import Mail, Message
from start import app

mail = Mail(app)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject, recipients=[to])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    mail.send(msg)
    return None

@app.context_processor
def cookies_check():
    value = request.cookies.get('cookie_consent')
    return dict(cookies_check = value == 'true')

