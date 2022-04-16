from flask_login import current_user
from flask import Blueprint, render_template, redirect, url_for, blueprints

from flask import flash
from .forms import MessageForm
from user.classes import User
from .functions import send_email


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

    return render_template('/pages/about.html', title_prefix = "FAQ" )


@other.route("/sendMessage", methods=['POST','GET'])
def sendMessage():

    if current_user.is_authenticated:
        form=MessageForm(name=current_user.name, lastName=current_user.lastName, mail=current_user.mail)
    else:
        form=MessageForm()

    if form.validate_on_submit():

        admins=User.query.filter(User.isAdmin == True).all()

        for admin in admins:
            send_email("admin@sportoweswiry.atthost24.pl", "Wiadomość od użytkownika {} {} - {}".format(form.name.data, form.lastName.data, form.subject.data),'message', 
                        name=form.name.data, lastName=form.lastName.data, mail=form.mail.data, message=form.message.data)

        
        flash("Wiadomość została wysłana. Odpowiemy najszybciej jak to możliwe.")
        return redirect(url_for('other.hello'))

    return render_template('/pages/sendMessage.html', form=form, title_prefix = "Formularz kontaktowy" )