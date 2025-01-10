from flask import url_for, render_template, redirect, flash
from flask_login import current_user, login_user, LoginManager, logout_user
from forms_wtf import LoginForm
from werkzeug.security import check_password_hash#Функции хеширования и проверки пароля
from app_db import app, Users, Profile
from UserLogin import UserLogin
from flask import Blueprint


login_bp = Blueprint('login_bp', __name__, url_prefix='/login')

login_manager = LoginManager(app)
login_manager.login_view = '/'

@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, Users, Profile)
    # return Users.query.get(int(user_id))  # Загружаем пользователя по ID

#Обработчик выхода из профиля
@login_bp.route("/logout")
def logout():
    logout_user()#Метод flask-login для выхода и очистки куки
    flash("Вы вышли из аккаунта", category="success")
    return redirect(url_for('login_bp.login'))


@login_bp.route("/", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
        return redirect(url_for('home'))

    form = LoginForm()  # Flask-WTF форма

    if form.validate_on_submit():
        user = Users.get_user_by_email(form.email.data)  # Используем метод из модели
        if user and check_password_hash(user.psw, form.psw.data):  # Проверяем пароль
            userLogin = UserLogin().create(user)
            print(userLogin)
            rm = form.remember.data
            login_user(userLogin, remember=rm)
            flash("Вы успешно вошли в систему.", category='success')
            return redirect(url_for("home"))
        flash("Неверная пара логин/пароль", category='danger')
    return render_template("login.html", title="Авторизация", form=form)