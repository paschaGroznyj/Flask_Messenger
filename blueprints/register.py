from flask import url_for, render_template, redirect, flash
from forms_wtf import RegisterForm
from werkzeug.security import generate_password_hash
from app_db import Users, Profile, db
import uuid # Генерация 128 битного username
from flask import Blueprint
from pathlib import Path
import os

DEFAULT_IMAGE_PATH = os.path.join(Path(__file__).parent.parent, "static", "images_html", "image", "img.png")

register_bp = Blueprint('register_bp', __name__, url_prefix='/register')

@register_bp.route('/', methods=["POST", "GET"])
def register():

    form = RegisterForm()
    if form.validate_on_submit():  # Проверка, а пришел ли запрос POST
        hash = generate_password_hash(form.psw.data)
        try:
            # Создаем нового пользователя
            u = Users(name=form.name.data, email=form.email.data, psw=hash)
            db.session.add(u)  # Добавляем в сессию
            db.session.flush()  # Перемещаем данные в таблицу для получения ID

            with open(DEFAULT_IMAGE_PATH, "rb") as f:
                image_bytes = f.read()
            # Создаем профиль пользователя
            profile = Profile(user_id=u.id,  # Связываем профиль с пользователем
                              nickname=f"user_{uuid.uuid4().hex[:8]}",
                              text_about="Этот пользователь пока ничего о себе не рассказал.",
                              image_pr=image_bytes)  # Устанавливаем начальные значения

            db.session.add(profile)  # Добавляем профиль в сессию
            db.session.commit()  # Сохраняем все изменения в БД

            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for("login_bp.login"))
        except Exception as e:
            db.session.rollback()  # Откат изменений в случае ошибки
            flash("Ошибка при добавлении в БД", "danger")
            print(f"Ошибка добавления в БД: {e}")

    return render_template("register.html", form=form)