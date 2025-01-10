from flask import url_for, request, render_template, redirect, jsonify
from flask_login import current_user, login_required
from app_db import Users, Chats, Profile, ChatMembers, PChats, db
from collections import deque
import base64
from DataHead import DataShapka
from flask import Blueprint


#Отображение в навбаре
menu = [{"url": "home", 'name': 'Home'},
        {"url": "profile_bp.profile", 'name': 'Профиль'},
        {"url": "chats_bp.page_chats", 'name': 'Чаты'},
        {"url": "search_bp.search", 'name': 'Поиск'}
        ]

chats_bp = Blueprint('chats_bp', __name__, url_prefix='/chats')

@chats_bp.route('/page_chats')
@login_required
def page_chats():

    personal = DataShapka()
    chats_data = personal.chat_data_func()

    return render_template('all_chats.html', menu=menu, chats_data=chats_data)


@chats_bp.route('/chats/<chat_id>')
@login_required
def chats(chat_id):
    # Проверка на подмену URL, а есть ли текущий пользователь в участниках чата
    is_member = ChatMembers.query.filter_by(link=chat_id, user_id=current_user.get_id()).first()

    if not is_member:
        return redirect(url_for("page_chats"))

    personal = DataShapka()
    chats_data = personal.chat_data_func(chat_id)
    return render_template('chats.html', menu = menu, chat_id = chat_id, chats_data = chats_data)



@chats_bp.route('/create/<int:person>', methods=['GET', 'POST'])
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
        return redirect(url_for('chats_bp.chats', chat_id = chat_id))

    # Если общего чата нет, создаем новый
    new_chat = PChats(group_or_not=False)
    db.session.add(new_chat)
    db.session.commit()  # Сохраняем новый чат, чтобы получить его ID

    # Добавляем обоих участников в новый чат
    member1 = ChatMembers(link=new_chat.id, user_id=current_user_id)
    member2 = ChatMembers(link=new_chat.id, user_id=person)
    db.session.add_all([member1, member2])
    db.session.commit()

    return redirect(url_for('chats_bp.chats', chat_id=new_chat.id)) # Перенаправление на новый чат



@chats_bp.route("/chats_request/<int:chat_id>", methods=["POST", "GET"])
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
        return "static/images_html/image/img.jpg"  # Аватар по умолчанию

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