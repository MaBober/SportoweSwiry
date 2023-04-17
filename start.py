from flask import Flask, render_template, current_app
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from config import Config
from werkzeug.exceptions import HTTPException

import logging
from logging.config import dictConfig
import datetime as dt

LOGGING_FILE_NAME = f'{dt.date.today()}.log'

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": os.path.join("logs", f'{str(dt.date.today())}.log'),
                "formatter": "default",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }
)

db = SQLAlchemy()
migrate = Migrate()

def create_app():

    app = Flask(__name__)
    
    app.logger.info("app created!")

    # app.config.from_pyfile('config.py')
    app.config.from_object(Config)
    migrate = Migrate(app, db)

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

    from flask_login import current_user

    if current_user.is_anonymous:
        current_app.logger.exception(f"User anonymous user generated error")
    
    else:
        current_app.logger.exception(f"User {current_user.id} generated error")

    if isinstance(error, HTTPException):
       return error
    
    return render_template("/pages/errors/500_generic.html", error=error), 500