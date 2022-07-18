from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config.from_pyfile('config.py')
    migrate = Migrate(app, db)

    app.config['SECRET_KEY'] ='SportoweSwiry22'

    #app.config['MAIL_SERVER']='smtp.gmail.com'
    #app.config['MAIL_PORT'] = 587
    #app.config['MAIL_USERNAME'] = 'sportowe.swiry.app@gmail.com'
    #app.config['MAIL_PASSWORD'] = 'BiegoweSwiry22'
    #app.config['MAIL_USE_TLS'] = True
    #app.config['MAIL_USE_SSL'] = False
    #app.config['MAIL_DEFAULT_SENDER'] = 'sportowe.swiry.app@gmail.com'


    app.config['MAIL_SERVER']='sportoweswiry.atthost24.pl'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'admin@sportoweswiry.atthost24.pl'
    app.config['MAIL_PASSWORD'] = 'BiegoweSwiry22'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_DEFAULT_SENDER'] = 'Sportowe Świry <admin@sportoweswiry.atthost24.pl>'

    app.config['AVATARS_SAVE_PATH'] = os.path.join(app.static_folder, 'avatars')

    db.init_app(app)
    migrate.init_app(app, db)

    return app

app = create_app()



@app.errorhandler(404)
def page_not_found(error):
   return render_template('/pages/errors/404.html'), 404


@app.errorhandler(Exception)
def handle_exception(error):

   if isinstance(error, HTTPException):
       return error

   return render_template("/pages/errors/500_generic.html", error=error), 500