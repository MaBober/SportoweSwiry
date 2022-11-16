from start import db
from event.classes import Participation


def delete_user_from_event(positionID, eventID):

    position = Participation.query.filter(Participation.event_id==eventID).filter(Participation.user_id == positionID).first()
    db.session.delete(position)
    db.session.commit()





