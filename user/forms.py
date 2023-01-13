
from flask_wtf import FlaskForm
from wtforms.fields import StringField, EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired

from .classes import User

MAX_AVATAR_SIZE_IN_MB = 5

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
    last_name=StringField("Nazwisko", validators=[DataRequired("Pole nie może być puste")])
    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie"), ValidateMailisExist])
    id=StringField("Login", validators=[DataRequired("Pole nie może być puste"), ValidateUserNameisExist])
    password=PasswordField("Hasło", validators=[DataRequired("Pole nie może być puste"), Length(min=8, message="Hasło nie może być krótsze niż 8 znaków")])
    verifyPassword=PasswordField("Potwierdź hasło", validators=[DataRequired("Pole nie może być puste"), ValidatePassword])
    isAdmin=BooleanField("Admin", default=False)
    avatar=BooleanField("Avatar", default=False)
    statute_acceptance=BooleanField("Akceptuję regulamin serwisu",validators=[DataRequired("Musisz zaakceptować regulamin!")], default=False)
    subscribe_newsletter = BooleanField("Zapisz się na newsletter.", default=False)


class VerifyEmailForm(FlaskForm):

    def ValidateMailisExist(form, field):
            tempMail = User.query.filter(User.mail==field.data).first()
            if not tempMail:
                raise ValidationError("Tego adresu email nie ma w naszej bazie danych")

    mail=EmailField("E-mail", validators=[DataRequired("Pole nie może być puste"), Email("Wpisz e-mail w poprawnej formie"), ValidateMailisExist])


class SubscribeNewsletter(FlaskForm):
    policy_acceptance=BooleanField("Akceptuję politykę prywatności serwisu",validators=[DataRequired("Musisz zaakceptować politykę prywatności!")], default=False)


class NewPasswordForm(FlaskForm):

    def ValidatePasswordIsCorrect(form, field):
        tempUser = User.query.filter(User.id==form.id.data).first()
        currentPassword=tempUser.password

        verify=tempUser.verify_password(field.data)

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

    def validate_login_is_correct(form, field):
        tempLogin = User.query.filter(User.id==field.data).first()
        tempMail = User.query.filter(User.mail==field.data).first()
        if (not tempMail) and (not tempLogin):
            raise ValidationError("Tego adresu e-mail nie ma w naszej bazie danych")

    def validate_password(self, field):

        temp_user_mail = User.query.filter(User.mail==self.name.data).first()
        temp_user_login = User.query.filter(User.id==self.name.data).first()
        if temp_user_mail != None:
            if (not temp_user_mail.verify_password(field.data)):
                raise ValidationError("Błędne dane logowania")
        if temp_user_login != None:
            if (not temp_user_login.verify_password(field.data)):
                raise ValidationError("Błędne dane logowania")

    name = StringField("Adres mailowy", validators=[validate_login_is_correct])
    password = PasswordField("Hasło", validators=[validate_password])
    remember = BooleanField("Zapamiętaj mnie", default=False)


class BanReason(FlaskForm):

    ban_reason = StringField("Hasło", validators=[DataRequired("Pole nie może być puste")])

class UploadAvatarForm(FlaskForm):

    def validate_avatar_size(form, field):
        #print(len(field.data.read()))
        #print(len(field.data.read()) > 1024)
        if len(field.data.read()) > MAX_AVATAR_SIZE_IN_MB * 1024 * 1024:
            raise ValidationError("Przesłany plik jest za duży")

    image = FileField('Wgraj zdjęcie (<=3MB)', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Zdjęcie może być wyłącznie w formacie .jpg lub .png'),
        validate_avatar_size])