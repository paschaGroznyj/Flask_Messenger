from flask_login import current_user
from app_db import app, Users, Chats, Profile, ChatMembers, PChats, db
from sqlalchemy import  and_
import base64

# Вывод информации по собеседнике в личных сообщениях или
# вывод информации и всех чатах текущего пользователя (Аватарки собеседника, последнее сообщение чата)
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
            db.session.query(Chats.link, Chats.text, Chats.created_at, Chats.user_id)  # link - это chat_id
            .filter(Chats.link.in_(friends_ids.values()))
            .group_by(Chats.link)
            .order_by(db.func.max(Chats.created_at).desc())  # Упорядочить по последнему сообщению
            .all()
        )

        messages_dict = {chat_id: f"{text}${created_at.strftime('%Y-%m-%d %H:%M')}${last_user_id}"
                         for chat_id, text, created_at, last_user_id in last_messages}

        chats_data = []


        for user_id, nickname, image in personal_data:
            last_message_data = messages_dict.get(int(friends_ids[user_id]), None)
            if not last_message_data: # Пропускаем пустые чаты
                continue
            last_message, date_time, last_user_id = last_message_data.rsplit('$', 2)
            if last_user_id == current_user_id:
                who = "Вы: "
            else:
                who = ''
            chats_data.append({
                "chat_id": friends_ids[user_id],
                "nickname": nickname,
                "image": f"data:image/png;base64,{base64.b64encode(image).decode('utf-8')}" if image else None,
                "last_message": last_message,
                "date_time": date_time,
                "who": who
            })
        # Конечная сортировка чатов по времени последних сообщений
        chats_data = sorted(chats_data, key=lambda x: x['date_time'], reverse=True)

        return chats_data