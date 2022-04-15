from flask_login import current_user
from flask import Blueprint, render_template, redirect, url_for, blueprints

other = Blueprint("other", __name__,
    template_folder='templates')

@other.route("/")
def hello():

    if current_user.is_authenticated and not current_user.confirmed:
        return redirect(url_for('unconfirmed'))

    if current_user.is_authenticated:
        return redirect(url_for('basicDashboard'))

    return render_template("pages/index.html", title_prefix = "Home")

@other.route("/faq")
def faq():

    return render_template('/pages/faq.html', title_prefix = "FAQ" )

@other.route("/about")
def about():

    return render_template('/pages/about.html', title_prefix = "FAQ" )