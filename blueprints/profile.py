from flask import url_for, request, render_template, redirect, flash, make_response
from flask_login import current_user, login_required
from app_db import app, Users, Chats, Profile, db
from werkzeug.utils import secure_filename
import base64
import re
from flask import Blueprint

#Отображение в навбаре
menu = [{"url": "home", 'name': 'Home'},
        {"url": "profile_bp.profile", 'name': 'Профиль'},
        {"url": "chats_bp.page_chats", 'name': 'Чаты'},
        {"url": "search_bp.search", 'name': 'Поиск'}
        ]

profile_bp = Blueprint('profile_bp', __name__, url_prefix='/profile')

@profile_bp.route("/")
@login_required
def profile():

        return render_template("profile.html", menu = menu)


@profile_bp.route("/<username>")
@login_required
def view_profile(username):
    if current_user.getNickname() == username:
        return render_template("profile.html", menu = menu)
    profile = Profile.query.filter_by(nickname = username).first()
    user = Users.query.get(profile.user_id) #Работа с первичным ключом
    counter = Chats.query.filter_by(user_id = profile.user_id).count()
    result = [{
                "name": user.name,
                "nickname": profile.nickname,
                "user_id": user.id,
                "image": f"data:image/png;base64,{base64.b64encode(profile.image_pr).decode('utf-8')}" if profile.image_pr else None,
                "about": profile.text_about,
                "counter_msg": counter
                        }]

    return render_template("view_profile.html", menu = menu, results = result)


@profile_bp.route("/userava")
@login_required
def userava():
    img = current_user.getAvatar(app)#Подгружаем пикчу из БД или аву по умолчанию
    if not img:
        return ''

    h = make_response(img)#Создаем ответ сервера для браузера
    h.headers["Content-Type"] = 'image/png'
    return h

@profile_bp.route("/upload", methods = ["POST", "GET"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files['file']#Получим файл из запроса
        filename = secure_filename(file.filename)#Метод werkzeug для защиты от опасных имен файлов
        if file and current_user.verifyExt(filename):#Проверка расширения файла png
            try:
                img = file.read()
                res = Profile.update_ava(current_user.get_id(), img)
                print(res)
                if not res:
                    flash("Ошибка обновления аватара", category='error')
                else:
                    flash("Аватар обновлен", "success")

                db.session.commit()  # Сохраняет все изменения в БД

            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "danger")
        else:
            flash("Ошибка обновления аватара", category="danger")

    return redirect(url_for("profile_bp.profile"))



@profile_bp.route("/upload_info", methods = ["POST", "GET"])
@login_required
def upload_info():
    if request.method == "POST":
        name = request.form['name']
        about = request.form['about']
        nickname = request.form['nickname']
        user_id = current_user.get_id()

        if name:
            # С помощью регулярных выражений
            if 4 <= len(name) <= 50:
                # Проверяем имя регулярным выражением
                if re.fullmatch(r'[А-Яа-яЁёA-Za-z ]+', name):
                    u = Users.update_name(user_id, name)
                    flash("Имя успешно изменено", category="success")
                else:
                    flash("Имя может содержать только символы кириллицы, латиницы и пробела", category="danger")
            else:
                flash("Имя должно содержать от 4 до 50 символов", category="danger")

            # if len(name) in range(4, 50):
            #     flag = True
            #     for i in name:
            #         if ord(i) in range(1040, 1104) or ord(i) == 1105 or ord(i) in range(65, 123) or ord(i) == 32: #А-я, ё, A-z, space
            #             continue
            #         else:
            #             flag = False
            #             flash("Имя может содержать только символы кириллицы, латиницы и пробела", category="danger")
            #             break
            #     if flag:
            #         u = Users.update_name(user_id, name)
            #         flash("Имя успешно изменено", category="success")
            # else:######??????????
            #     flash("Имя должно содержать от 4 до 50 символов", category="danger")

        if about:
            if 4 <= len(about) <= 300:
                u = Profile.update_text(user_id, about)
                if u:
                    flash("Текст успешно изменен", category="success")
                else:
                    flash("Ошибка изменения имени", category="danger")

        if nickname:
            if 4 <= len(nickname) <= 30:
                # Проверка на уникальность
                if Profile.get_nickname(nickname):
                    flash("Этот ник уже занят", category="danger")
                else:
                    # Проверка регулярным выражением
                    if re.fullmatch(r'[a-z0-9_]+', nickname):
                        _ = Profile.update_nickname(user_id, nickname)
                        flash("Никнейм успешно изменен", category="success")
                    else:
                        flash("Никнейм может содержать только символы a-z, 0-9 или _", category="danger")
            else:
                flash("Никнейм должен содержать от 4 до 30 символов", category="danger")

    return redirect(url_for("profile_bp.profile"))