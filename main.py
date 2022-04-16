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


if __name__ == "__main__":
    app.debug = True
    app.run()
