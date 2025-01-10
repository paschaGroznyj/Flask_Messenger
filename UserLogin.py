from flask_login import UserMixin #Передаем в наследование методы по умолчанию
from flask import url_for
class UserLogin(UserMixin):
    def fromDB(self, user_id, Users, Profile):
        self.__user = Users.query.get(int(user_id))
        self.__profile = Profile.query.filter_by(user_id=user_id).first()
        if not self.__profile:
            print(f"Профиль пользователя с ID {user_id} не найден.")
        return self

    def create(self, user):
        self.__user  = user
        return self
    # Эти методы уже передаются при наследовании, самому прописывать необязательно
    def is_authenticated(self):
        return True
    # def is_active(self):
    #     return True
    # def is_anon(self):
    #     return False
    def get_id(self):
        return str(self.__user.id)

    def getName(self):
        return self.__user.name if self.__user else "Без имени"

    def getNickname(self):
        return self.__profile.nickname if self.__profile else "Без имени"

    def getAbout(self):
        return self.__profile.text_about if self.__profile else "Без имени"

    def getEmail(self):
        return self.__user.email if self.__user else "Без email"


    def getAvatar(self, app):
        if not self.__profile:
            print("Профиль отсутствует")
            return None
        img = None
        if not self.__profile.image_pr:
            try:
                with app.open_resource(app.root_path + url_for("static", filename="images_html/image/img.jpg"),
                                       "rb") as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("Не найден аватар по умолчанию: " + str(e))
        else:
            img = self.__profile.image_pr
        return img

    def verifyExt(self, filename):
        file_ext = ['png', 'jpg']
        ext = filename.rsplit('.', 1)[1].lower()#деление строчки начинает справа, делает одно разбиение и берет расширение пример img_1.png = ['img_1', 'png']
        if ext in file_ext:
            return True
        return False