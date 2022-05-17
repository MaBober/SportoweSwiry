from flask_wtf import FlaskForm
from wtforms.fields import StringField, EmailField, TextAreaField, DateField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired, Email




class MessageForm(FlaskForm):
    name=StringField("Imię", validators=[DataRequired("Pole nie może być puste")])
    lastName=StringField("Nazwisko", validators=[DataRequired("Pole nie może być puste")])
    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie")])
    subject=StringField("Temat", validators=[DataRequired("Pole nie może być puste")])
    message = TextAreaField("Wiadomość", validators=[DataRequired("Pole nie może być puste")])


class AppMailForm(FlaskForm):
    receiverEmail=SelectMultipleField("Odbiorca/y", choices=[])
    subject=StringField("Temat", validators=[DataRequired("Pole nie może być puste")])
    message = TextAreaField("Wiadomość", validators=[DataRequired("Pole nie może być puste")])
    sendByApp=BooleanField("Wiadomość w aplikacji", default=True)
    sendByEmail=BooleanField("Wiadomość na maila", default=False)