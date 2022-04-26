from .classes import User
from flask_wtf import FlaskForm
from wtforms.fields import StringField, EmailField, PasswordField, BooleanField, DecimalField, DateField, IntegerField, SelectField, DateTimeField, SubmitField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, ValidationError, NumberRange, InputRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired


#Definition class for User - WTF-FlaskForm
class UserForm(FlaskForm):

    def ValidateMailisExist(form, field):
        tempMail = User.query.filter(User.mail==field.data).first()
        if tempMail:
            raise ValidationError("Ten adres email jest już w użyciu")

    def ValidateUserNameisExist(form, field):
        tempUserName = User.query.filter(User.id==field.data).first()
        if tempUserName:
            raise ValidationError("Ten Login jest już w użyciu")
        
    def ValidatePassword(form, field):
        if field.data!=form.password.data:
            raise ValidationError("Wpisane hasła muszą być identyczne")


    name=StringField("Imię", validators=[DataRequired("Pole nie może być puste")])
    lastName=StringField("Nazwisko", validators=[DataRequired("Pole nie może być puste")])
    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie"), ValidateMailisExist])
    id=StringField("Login", validators=[DataRequired("Pole nie może być puste"), ValidateUserNameisExist])
    password=PasswordField("Hasło", validators=[DataRequired("Pole nie może być puste"), Length(min=8, message="Hasło nie może być krótsze niż 8 znaków")])
    verifyPassword=PasswordField("Potwierdź hasło", validators=[DataRequired("Pole nie może być puste"), ValidatePassword])
    isAdmin=BooleanField("Admin", default=False)
    avatar=BooleanField("Avatar", default=False)


class VerifyEmailForm(FlaskForm):

    def ValidateMailisExist(form, field):
            tempMail = User.query.filter(User.mail==field.data).first()
            if not tempMail:
                raise ValidationError("Tego adresu email nie ma w naszej bazie danych")

    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie"), ValidateMailisExist])


class NewPasswordForm(FlaskForm):

    def ValidatePasswordIsCorrect(form, field):
        tempUser = User.query.filter(User.id==form.userName.data).first()
        currentPassword=tempUser.password

        verify=User.verify_password(currentPassword, field.data)

        if not verify:
            raise ValidationError("Podaj poprawne aktulane hasło")

    def ValidatePassword(form, field):
        if field.data!=form.newPassword.data:
            raise ValidationError("Wpisane nowe hasła muszą być identyczne")


    id=StringField("Login")
    oldPassword=PasswordField("Obecne hasło", validators=[DataRequired("Pole nie może być puste"), ValidatePasswordIsCorrect])
    newPassword=PasswordField("Nowe hasło", validators=[DataRequired("Pole nie może być puste"), Length(min=8, message="Hasło nie może być krótsze niż 8 znaków")])
    verifyNewPassword=PasswordField("Potwierdź nowe hasło", validators=[DataRequired("Pole nie może być puste"), Length(min=8, message="Hasło nie może być krótsze niż 8 znaków"), ValidatePassword])

#Definition class for LOGIN function
class LoginForm(FlaskForm):

    def ValidateLoginIsCorrect(form, field):
        tempLogin = User.query.filter(User.id==field.data).first()
        tempMail = User.query.filter(User.mail==field.data).first()
        if (not tempMail) and (not tempLogin):
            raise ValidationError("Tego loginu/adresu email nie ma w naszej bazie danych")

    name=StringField("Login lub adres mailowy", validators=[ValidateLoginIsCorrect])
    password=PasswordField("Hasło")
    remember=BooleanField("Zapamiętaj mnie")


class UploadAvatarForm(FlaskForm):
    image = FileField('Wgraj zdjęcie (<=3MB)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Zdjęcie może być wyłącznie w formacie .jpg lub .png')])