from flask import Flask, session ,url_for, request, render_template, redirect, flash, jsonify, make_response
from flask_login import current_user, login_user, LoginManager, login_required, logout_user
from forms_wtf import LoginForm, RegisterForm, Chat
from werkzeug.security import generate_password_hash, check_password_hash#Функции хеширования и проверки пароля
from flask_sqlalchemy import SQLAlchemy
from app_db import app, Users, Chats, Profile, ChatMembers, PChats, db
from UserLogin import UserLogin
from werkzeug.utils import secure_filename
from sqlalchemy import desc, or_, and_
from collections import deque
import base64
import re
import uuid # Генерация 128 битного username


#Отображение в навбаре
menu = [{"url": "home", 'name': 'Home'},
        {"url": "profile", 'name': 'Профиль'},
        {"url": "page_chats", 'name': 'Чаты'},
        {"url": "search", 'name': 'Поиск'}
        ]


login_manager = LoginManager(app)
login_manager.login_view = '/'

@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, Users, Profile)
    # return Users.query.get(int(user_id))  # Загружаем пользователя по ID

#Обработчик выхода из профиля
@app.route("/logout")
def logout():
    logout_user()#Метод flask-login для выхода и очистки куки
    flash("Вы вышли из аккаунта", category="success")
    return redirect(url_for('login'))


@app.route('/register', methods=["POST", "GET"])
def register():

    form = RegisterForm()
    if form.validate_on_submit():  # Проверка, а пришел ли запрос POST
        hash = generate_password_hash(form.psw.data)
        try:
            # Создаем нового пользователя
            u = Users(name=form.name.data, email=form.email.data, psw=hash)
            db.session.add(u)  # Добавляем в сессию
            db.session.flush()  # Перемещаем данные в таблицу для получения ID

            # Создаем профиль пользователя
            profile = Profile(user_id=u.id,  # Связываем профиль с пользователем
                              nickname=f"user_{uuid.uuid4().hex[:8]}",
                              text_about="Этот пользователь пока ничего о себе не рассказал.",
                              image_pr=None)  # Устанавливаем начальные значения

            db.session.add(profile)  # Добавляем профиль в сессию
            db.session.commit()  # Сохраняем все изменения в БД

            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()  # Откат изменений в случае ошибки
            flash("Ошибка при добавлении в БД", "danger")
            print(f"Ошибка добавления в БД: {e}")

    return render_template("register.html", form=form)


@app.route("/", methods=["POST", "GET"])
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
        flash("Неверная пара логин/пароль", category='error')
    return render_template("login.html", title="Авторизация", form=form)


@app.route("/home")
@login_required
def home():
        return render_template("home.html", menu = menu)


@app.route("/profile")
@login_required
def profile():

        return render_template("profile.html", menu = menu)



@app.route("/profile/<username>")
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


class DataShapka:
    def chat_data_func(self, chat_id=None):
        current_user_id = current_user.get_id()

        if not chat_id: # Выводим все чаты текущего пользователя
            friends = (
                db.session.query(ChatMembers.user_id, PChats.id.label("chat_id"))
                .join(PChats, ChatMembers.link == PChats.id)
                .filter(
                    ChatMembers.link.in_(
                        db.session.query(ChatMembers.link).filter_by(user_id=current_user_id)
                    )
                )
                .filter(ChatMembers.user_id != current_user_id)
                .all()
            )
            friends_ids = {friend.user_id: friend.chat_id for friend in friends}

        else: # Показываем шапку чата
            friends = (
                db.session.query(ChatMembers.user_id)
                .filter(
                    and_(
                        ChatMembers.link == chat_id,
                        ChatMembers.user_id != current_user_id
                    )
                )
                .all()
            )
            friends_ids = {friend.user_id: chat_id for friend in friends}



        # Получить персональные данные друзей
        personal_data = (
            db.session.query(Profile.user_id, Profile.nickname, Profile.image_pr)
            .filter(Profile.user_id.in_(friends_ids.keys()))
            .all()
        )

        # Получить последние сообщения для каждого чата
        last_messages = (
            db.session.query(Chats.link, Chats.text, Chats.created_at)  # link - это chat_id
            .filter(Chats.link.in_(friends_ids.values()))
            .group_by(Chats.link)
            .order_by(db.func.max(Chats.created_at).desc())  # Упорядочить по последнему сообщению
            .all()
        )

        messages_dict = {chat_id: f"{text}${created_at}" for chat_id, text, created_at in last_messages}

        chats_data = []
        for user_id, nickname, image in personal_data:
            last_message_data = messages_dict.get(int(friends_ids[user_id]), None)
            if not last_message_data: # Пропускаем пустые чаты
                continue
            last_message, date_time = last_message_data.rsplit('$', 1)
            chats_data.append({
                "chat_id": friends_ids[user_id],
                "nickname": nickname,
                "image": f"data:image/png;base64,{base64.b64encode(image).decode('utf-8')}" if image else None,
                "last_message": last_message,
                "date_time": date_time,
            })
        return chats_data




@app.route('/page_chats')
@login_required
def page_chats():

    personal = DataShapka()
    chats_data = personal.chat_data_func()

    return render_template('all_chats.html', menu=menu, chats_data=chats_data)


@app.route('/chats/<chat_id>')
@login_required
def chats(chat_id):
    # Проверка на подмену URL, а есть ли текущий пользователь в участниках чата
    is_member = ChatMembers.query.filter_by(link=chat_id, user_id=current_user.get_id()).first()

    if not is_member:
        return redirect(url_for("page_chats"))

    personal = DataShapka()
    chats_data = personal.chat_data_func(chat_id)
    return render_template('chats.html', menu = menu, chat_id = chat_id, chats_data = chats_data)



@app.route('/create/<int:person>', methods=['GET', 'POST'])
@login_required
def create_chat(person):
    # Найти ID текущего пользователя
    current_user_id = current_user.get_id()

    # Найти чаты текущего пользователя
    current_user_chats = (
        db.session.query(ChatMembers.link)
        .filter(ChatMembers.user_id == current_user_id)
        .all()
    )
    current_user_chat_ids = [chat.link for chat in current_user_chats]
    # Найти чаты другого пользователя
    person_chats = (
        db.session.query(ChatMembers.link)
        .filter(ChatMembers.user_id == person)
        .all()
    )
    person_chat_ids = [chat.link for chat in person_chats]
    # Найти общий чат
    common_chat_ids = set(current_user_chat_ids) & set(person_chat_ids)
    # Проверить, есть ли общий чат
    common_chat = None
    if common_chat_ids:
        common_chat = list(common_chat_ids)[0]
    # Найти общие чаты
    # common_chat = (
    #     db.session.query(ChatMembers.link)
    #     .filter(ChatMembers.user_id == current_user_id)
    #     .filter(ChatMembers.link.in_(
    #         db.session.query(ChatMembers.link).filter(ChatMembers.user_id == person)
    #     ))
    #     .first()
    # )
    """SELECT link
    FROM ChatMembers
    WHERE link IN (SELECT link FROM ChatMembers WHERE user_id = current_user_id)
    AND link IN (SELECT link FROM ChatMembers WHERE user_id = person_id)
    LIMIT 1;"""

    # Если общий чат найден
    if common_chat:
        chat_id = common_chat
        return redirect(url_for('chats', chat_id = chat_id))

    # Если общего чата нет, создаем новый
    new_chat = PChats(group_or_not=False)
    db.session.add(new_chat)
    db.session.commit()  # Сохраняем новый чат, чтобы получить его ID

    # Добавляем обоих участников в новый чат
    member1 = ChatMembers(link=new_chat.id, user_id=current_user_id)
    member2 = ChatMembers(link=new_chat.id, user_id=person)
    db.session.add_all([member1, member2])
    db.session.commit()

    return redirect(url_for('chats', chat_id=new_chat.id)) # Перенаправление на новый чат



@app.route("/chats_request/<int:chat_id>", methods=["POST", "GET"])
@login_required
def chats_request(chat_id):
    chat_id = chat_id
    if request.method == "POST":
        if request.is_json:
            data = request.json
            new_message = Chats(text=data['message'], user_id=current_user.get_id(), link = chat_id)
            db.session.add(new_message)
            db.session.commit()
            return jsonify(status='success'), 200

    if chat_id is None:
        messages = Chats.query.filter(Chats.link.is_(None)).order_by(Chats.created_at).limit(100).all()
    else:
        messages = Chats.query.filter_by(link=chat_id).order_by(Chats.created_at).limit(100).all()

    formatted_messages = []

    formatted_messages.append({
        "user_real_time": current_user.getName(),
        "id_user_real_time": current_user.get_id()
    })

    # Переменная для отслеживания последнего обработанного пользователя
    last_user_id = None
    message_group = deque()  # Для хранения сообщений текущей группы

    def get_avatar(user_id):
        """Получение аватарки пользователя"""
        user_avatar = Profile.query.filter_by(user_id=user_id).first()
        if user_avatar and user_avatar.image_pr:
            return f"data:image/png;base64,{base64.b64encode(user_avatar.image_pr).decode('utf-8')}"
        return "static/images_html/image/img.png"  # Аватар по умолчанию

    def add_group_messages(group, last_user_id):
        """Форматирование группы сообщений одного пользователя"""
        user_info = Users.query.get(last_user_id)  # Работает только с первичным ключом
        user_name = "Me" if user_info.name == current_user.getName() else user_info.name
        avatar_url = get_avatar(last_user_id)

        for i, msg in enumerate(group):
            formatted_message = {
                "message": msg.text,
                "user_id": msg.user_id,
                "created_at": msg.created_at.strftime('%H:%M'),
                "user_name": user_name if i == 0 or user_name == "Me" else "",  # Имя только у первого сообщения
                "avatar": avatar_url if i == len(group) - 1 else ""  # Аватар только у последнего
            }
            formatted_messages.append(formatted_message)

    # Основной цикл
    for message in messages:
        if message.user_id != last_user_id:

            if message_group:
                add_group_messages(message_group, last_user_id)
                message_group.clear()

            last_user_id = message.user_id

        message_group.append(message)

    if message_group:
        add_group_messages(message_group, last_user_id)


    return jsonify(messages=formatted_messages), 200


@app.route("/userava")
@login_required
def userava():
    img = current_user.getAvatar(app)#Подгружаем пикчу из БД или аву по умолчанию
    if not img:
        return ''

    h = make_response(img)#Создаем ответ сервера для браузера
    h.headers["Content-Type"] = 'image/png'
    return h

@app.route("/upload", methods = ["POST", "GET"])
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

    return redirect(url_for("profile"))



@app.route("/upload_info", methods = ["POST", "GET"])
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
            if 4 <= len(nickname) <= 300:
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

    return redirect(url_for("profile"))



@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
    string_ = None
    final_result = None

    if request.method == "POST":
        string_ = request.form['name_nickname'].strip()
        # string_ = string_.lower() тут изначально нужно было добавить столбец в БД для lower имен
        print(string_)
        if not string_:
            flash("Поле поиска не должно быть пустым!", category="danger")
            return render_template("search.html", menu=menu, results=None)

        if string_.startswith("@"):
            # Поиск по никнейму с объединением
            results = (
                db.session.query(Users.name, Profile.nickname, Profile.image_pr)
                .join(Profile, Users.id == Profile.user_id)
                .filter(Profile.nickname.ilike(f"%{string_[1:]}%"))
                .all()
            )
        else:
            # Поиск по имени с объединением
            results = (
                db.session.query(Users.name, Profile.nickname, Profile.image_pr)
                .join(Profile, Users.id == Profile.user_id)
                .filter(Users.name.ilike(f"%{string_}%"))
                .all()
            )

        final_result = [{
                "name": name,
                "nickname": nickname,
                "image": f"data:image/png;base64,{base64.b64encode(image).decode('utf-8')}" if image else None,
                        }
                        for name, nickname, image in results]

        if not final_result:
            flash(f"Пользователи с именем или никнеймом '{string_}' не найдены.", category="danger")

    return render_template("search.html", menu=menu, results=final_result)



if __name__ == "__main__":
        app.run(host="0.0.0.0", port = 5000, debug=True)