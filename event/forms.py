from flask_wtf import FlaskForm
from wtforms.fields import StringField, BooleanField, DecimalField, DateField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, NumberRange,NumberRange, ValidationError

from .classes import Event
from activity.classes import Sport

import datetime as dt


class EventForm(FlaskForm):

    def validate_date (form, field):
        today = dt.date.today()
        if field.data <= today:
            raise ValidationError("Wybierz przyszłą datę")

    def validate_name_is_free(form, field):
        name_to_check = Event.query.filter(Event.status != '5').filter(Event.name == field.data).first()
        if field.data == form.old_name.data:
            pass
        elif name_to_check != None:
            raise ValidationError("Istnieje już aktywne wyzwanie o takiej nazwie. Wybierz proszę inną nazwę.")

    def validate_participants_amount(form,field):
        if form.participatns.data != None and field.data < form.participatns.data:
            raise ValidationError(f'Do wyzwania już zapisało się {form.participatns.data} uczestników. Wybierz większą liczbę.')

    name = StringField("Nazwa", validators=[DataRequired("Pole nie może być puste"), validate_name_is_free])
    start = DateField("Data rozpoczęcia", validators=[DataRequired("Pole nie może być puste"), validate_date])
    length = IntegerField("Długość w tygodniach", validators = [NumberRange(min = 1, max= 15, message = "Podaj proszę liczbę nie ujemną!")], default = 10)
    isPrivate = BooleanField("Wydarzenie prywatne")
    password=StringField("Hasło")
    description = TextAreaField("Opis wyzwania")
    max_users = IntegerField("Maksymalna ilośc uczestników", validators = [NumberRange(min = 1, max= 25, message = "Podaj proszę liczbę większą od zera!"), validate_participants_amount], default = 10)
    old_name =  StringField("Nazwa")
    participatns = IntegerField("Zapisanych uczestników")

class EventPassword(FlaskForm):

    password = StringField("Hasło")


class CoeficientsForm(FlaskForm):

    def validate_name(form, field):
        print(field.data)
        if Sport.query.filter(Sport.name == field.data).first() is not None:
            raise ValidationError("Istnieje już sport o takiej nazwie. Wybierz proszę inną nazwę.")
        else:
            pass

    def validate_strava_name(form, field):
        if Sport.query.filter(Sport.strava_name == field.data).first() is not None and field.data != "":
            raise ValidationError("Istnieje już sport o takiej nazwie w strava. Wybierz proszę inną nazwę Strava.")
        else:
            pass            


    event_name = StringField("Wyzwanie", validators=[DataRequired("Pole nie może być puste")])
    activity_name = StringField("Nazwa aktywności", validators=[DataRequired("Pole nie może być puste"), validate_name])
    is_constant = SelectField("Stała / Współczynnik", choices =[(1, "Stała"), (0, "Współczynnik")])
    strava_name = StringField("Nazwa aktywności w Strava [ENG]", validators=[validate_strava_name])
    value = DecimalField("Wartość", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1)

class NewSportToEventForm(FlaskForm):
    
    activity_type = SelectField("Wybierz sport", validators=[NumberRange(min=0, message="Wybierz pozycję z listy!")], default=1, choices=[])


class DistancesForm(FlaskForm):

    w1 = DecimalField("Tydzień 1", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w2 = DecimalField("Tydzień 2", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w3 = DecimalField("Tydzień 3", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w4 = DecimalField("Tydzień 4", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w5 = DecimalField("Tydzień 5", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w6 = DecimalField("Tydzień 6", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w7 = DecimalField("Tydzień 7", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w8 = DecimalField("Tydzień 8", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w9 = DecimalField("Tydzień 9", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w10 = DecimalField("Tydzień 10", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w11 = DecimalField("Tydzień 11", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w12 = DecimalField("Tydzień 12", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w13 = DecimalField("Tydzień 13", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w14 = DecimalField("Tydzień 14", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    w15 = DecimalField("Tydzień 15", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)