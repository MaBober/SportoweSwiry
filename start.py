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

    app.config['FLASK_APP']='main'
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