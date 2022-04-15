from flask_wtf import FlaskForm
from wtforms.fields import StringField, BooleanField, DecimalField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange,NumberRange


class EventForm(FlaskForm):

    name = StringField("Nazwa")

    start = DateField("Data rozpoczęcia")
    length = IntegerField("Długość w tygodniach", validators=[NumberRange(min=0, max=15, message="Podaj proszę liczbę nie ujemną!")], default=10)

    #adminID = IntegerField("ID administratora", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1)
    adminID = SelectField("Administrator wyzwania", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1, choices=[])

    isPrivate =BooleanField("Wydarzenie prywatne")
    isSecret = BooleanField("Wydarenie ukryte")
    status = SelectField("Status wyzwania", validators=[NumberRange(min=0, message="Wybierz pozycję z listy!")], default=1, choices=[])

    #coefficientsTable_id = IntegerField("ID tablicy ze wspołczynnikami", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1)
    coefficientsSetName = SelectField("ID tablicy ze wspołczynnikami", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1, choices=[])

class CoeficientsForm(FlaskForm):

    setName = StringField("Nazwa zestawu współczynników", validators=[DataRequired("Pole nie może być puste")])
    activityName = StringField("Nazwa aktywności", validators=[DataRequired("Pole nie może być puste")])
    constant = BooleanField("Stała wartość?", default=False)
    value = DecimalField("Współczynnik", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=1)
    
class NewCoeficientsSetForm(FlaskForm):

    setName = StringField("Nazwa zestawu współczynników", validators=[DataRequired("Pole nie może być puste")])

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