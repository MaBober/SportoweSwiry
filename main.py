from start import app, db
from startupFunctions import checkIfIsAdmin
from event.functions import createCofficientTemplate

from user.routes import user
from other.routes import other
from event.routes import event
from activity.routes import activity

app.register_blueprint(user)
app.register_blueprint(other)
app.register_blueprint(event)
app.register_blueprint(activity)

app.debug = True


@app.before_first_request
def appStartup():
    db.create_all()
    checkIfIsAdmin()
    createCofficientTemplate()

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


if __name__ == "__main__":
    app.debug = True
    app.run()
