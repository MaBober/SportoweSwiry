from flask_wtf import FlaskForm
from wtforms.fields import StringField, EmailField, TextAreaField, DateField, SelectMultipleField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, ValidationError




class MessageForm(FlaskForm):
    name=StringField("Imię", validators=[DataRequired("Pole nie może być puste")])
    last_name=StringField("Nazwisko", validators=[DataRequired("Pole nie może być puste")])
    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie")])
    subject=StringField("Temat", validators=[DataRequired("Pole nie może być puste")])
    message = TextAreaField("Wiadomość", validators=[DataRequired("Pole nie może być puste")])


class AppMailForm(FlaskForm):

    def ValidateSendByApp(form, field):
        if not field.data and not form.send_by_email.data:
            raise ValidationError("Minimum jedna opcja musi być zaznaczona")

    receiver_email=SelectField("Adresat", choices=[])
    subject=StringField("Temat", validators=[DataRequired("Pole nie może być puste")], default="")
    message = TextAreaField("Wiadomość", validators=[DataRequired("Pole nie może być puste")], default="")
    send_by_app=BooleanField("Wiadomość w aplikacji", default=True, validators=[ValidateSendByApp])
    send_by_email=BooleanField("Wiadomość na maila", default=False)


class AppMailToRead(FlaskForm):
    sender=StringField("Adresat", default="")
    subject=StringField("Temat", default="")
    message = StringField("Wiadomość", default="")