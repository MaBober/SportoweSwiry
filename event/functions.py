from start import db
from event.classes import Participation


def delete_user_from_event(positionID, eventID):

    position = Participation.query.filter(Participation.event_id==eventID).filter(Participation.user_id == positionID).first()
    db.session.delete(position)
    db.session.commit()

def add_user_to_event(user_id, eventID):

    participation = Participation(user_id = user_id, event_id = eventID)
    db.session.add(participation)
    db.session.commit()

    return None




