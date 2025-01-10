from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField#Для работы с полем ввода, для кнопки, для чек бокса, для пароля
from wtforms.validators import DataRequired, Email, Length, EqualTo#проверка соответствия паролей

class LoginForm(FlaskForm):
    email = StringField("Email: ", validators=[Email("Некорректный email")])
    psw = PasswordField("Пароль: ", validators=[DataRequired(), Length(min=4, max=100, message="Пароль должен быть длиннее")])
    remember = BooleanField("Запомнить", default=False)
    submit = SubmitField("Войти")

class RegisterForm(FlaskForm):
    name = StringField("Имя ", validators=[Length(min=4, max=100, message="Имя должно быть от 4 до 100 символов")])
    email = StringField("Email ", validators=[Email("Некорректный email")])
    psw = PasswordField("Пароль ", validators=[DataRequired(), Length(min=4, max=100, message="Пароль должен быть длиннее")])
    psw2 = PasswordField("Повтор пароля ", validators=[DataRequired(), EqualTo("psw", message="Пароли не совпадают")])#Вернет True or False
    submit = SubmitField("Регистрация")

class Chat(FlaskForm):
    msg = StringField("Сообщение ")
    submit = SubmitField("Отправить")
