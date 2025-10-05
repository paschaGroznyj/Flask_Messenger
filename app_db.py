from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime
from config import DB_SETTING

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fddmvkdmvkmvskdfsdkvm'
app.config.from_object(__name__)#Подгружаем нашу конфигурацию во Flask

db = SQLAlchemy()

# Конфигурация приложения
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = (f'postgresql://{DB_SETTING["DB_USER"]}:{DB_SETTING["DB_PASSWORD"]}'
                                        f'@{DB_SETTING["DB_HOST"]}:{DB_SETTING["DB_PORT"]}/{DB_SETTING["DB_NAME"]}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Связываем SQLAlchemy с приложением
db.init_app(app)

# Основная таблица Юзеров
class Users(db.Model):#превращаем таблицу Users в набор таблицы SQLAlchemy
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50), nullable=True)
    psw = db.Column(db.String(500), nullable=True)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    pr = db.relationship('Chats', backref='users', uselist=False)

    pr2 = db.relationship('Profile', backref='users', uselist=False)
    # pr = db.relationship('Profiles', backref = 'users', uselist = False)#Через переменную будет устанавливаться связь с таблицей Profiles
    #backref указывает таблицу куда подсоединяются данные из таблицы Profiles
    #uselist = False одна запись таблицы соответсвует другой таблице
    @staticmethod
    def get_user_by_email(email):
        return Users.query.filter_by(email=email).first()  # Стандартный запрос значения по критерию

    @staticmethod
    def update_name(user_id, name):
        try:
            user = Users.query.filter_by(id=user_id).first()  # Находим пользователя по user_id
            print(f"id Пользователя для изменения имени {user_id}")
            if user:
                user.name = name  # Обновляем поле image_pr в записи пользователя
                db.session.commit()  # Сохраняем изменения
                return True
            return False  # Если пользователь не найден
        except Exception as e:
            print(f"Ошибка обновления имени через SQLAlchemy: {e}")
            db.session.rollback()  # Откатываем изменения в случае ошибки
            return False


    def __repr__(self):
        return f"<users {self.id}>"




class PChats(db.Model): #Таблица для идентификации всех чатов
    __tablename__ = 'pchats'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key = True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    group_or_not = db.Column(db.Boolean, default = False) #Групповой чат или лс

    pr = db.relationship('ChatMembers', backref = 'pchats', lazy = True)

class ChatMembers(db.Model): #Участники чатов
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key = True)
    link = db.Column(db.Integer, db.ForeignKey('pchats.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Chats(db.Model): # Таблица хранения сообщений и отношений с чатами
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.Integer, db.ForeignKey('pchats.id')) #Подвязываем чат к тексту участников
    text = db.Column(db.String(2000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Profile(db.Model): # Таблица профилей Юзеров с аватарками, текстами о себе, никнеймами
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    image_pr = db.Column(db.LargeBinary, nullable = False)
    text_about = db.Column(db.Text, nullable = False)
    nickname = db.Column(db.Text, nullable = False)

    @staticmethod
    def get_nickname(nickname):
        return Profile.query.filter_by(nickname=nickname).first()

    @staticmethod
    def update_ava(user_id, img):
        try:
            user = Profile.query.filter_by(user_id=user_id).first()  # Находим пользователя по user_id
            print(f"id Пользователя {user_id}")
            if user:
                user.image_pr = img  # Обновляем поле image_pr в записи пользователя
                db.session.commit()  # Сохраняем изменения
                return True
            return False  # Если пользователь не найден
        except Exception as e:
            print(f"Ошибка обновления аватара через SQLAlchemy: {e}")
            db.session.rollback()  # Откатываем изменения в случае ошибки
            return False

    @staticmethod
    def update_text(user_id, text):
        try:
            user = Profile.query.filter_by(user_id=user_id).first()  # Находим пользователя по user_id
            print(f"id Пользователя для изменения текста {user_id}")
            if user:
                user.text_about = text  # Обновляем поле image_pr в записи пользователя
                db.session.commit()  # Сохраняем изменения
                return True
            return False  # Если пользователь не найден
        except Exception as e:
            print(f"Ошибка обновления текста через SQLAlchemy: {e}")
            db.session.rollback()  # Откатываем изменения в случае ошибки
            return False

    @staticmethod
    def update_nickname(user_id, nickname):
        try:
            user = Profile.query.filter_by(user_id=user_id).first()  # Находим пользователя по user_id
            print(f"id Пользователя для изменения никнейма {user_id}")
            if user:
                user.nickname = nickname  # Обновляем поле image_pr в записи пользователя
                db.session.commit()  # Сохраняем изменения
                return True
            return False  # Если пользователь не найден
        except Exception as e:
            print(f"Ошибка обновления текста через SQLAlchemy: {e}")
            db.session.rollback()  # Откатываем изменения в случае ошибки
            return False

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Таблицы созданы")