#from datetime import datetime
import datetime

from start import db
from flask_wtf import FlaskForm
from wtforms.fields import StringField, EmailField, DecimalField, DateField, SelectField, DateTimeField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError, NumberRange, InputRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired




# Defines form for activities
class ActivityForm(FlaskForm):

    def ValidateFutureDate (form, field):
        today=datetime.date.today()
        if field.data>today:
            raise ValidationError("Nie możesz podać daty z przyszłości")

    date = DateField("Data aktywności", validators=[InputRequired("Musisz podać date"), ValidateFutureDate], default=datetime.date.today())
    activity = SelectField("Rodzaj aktywności", default=1, choices=[])
    distance = DecimalField("Dystans", validators=[NumberRange(min=0, message="Podaj proszę liczbę nie ujemną!")], default=0)
    time = DateTimeField("Czas", format='%H:%M:%S', default=datetime.time(), validators=[DataRequired(message='Podaj proszę czas w formacie HH:MM:SS')])

    def fill_sports_to_select(self):

        from activity.classes import Sport

        self.activity.choices = Sport.all_sports()


class UploadAvatarForm(FlaskForm):
    image = FileField('Wgraj zdjęcie (<=3MB)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Zdjęcie może być wyłącznie w formacie .jpg lub .png')])

class MessageForm(FlaskForm):
    name=StringField("Imię", validators=[DataRequired("Pole nie może być puste")])
    lastName=StringField("Nazwisko", validators=[DataRequired("Pole nie może być puste")])
    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie")])
    subject=StringField("Temat", validators=[DataRequired("Pole nie może być puste")])
    message = TextAreaField("Wiadomość", validators=[DataRequired("Pole nie może być puste")])

