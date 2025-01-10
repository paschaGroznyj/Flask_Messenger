from flask import request, render_template, flash
from flask_login import  login_required
from app_db import Users, Profile, db
import base64
from flask import Blueprint


#Отображение в навбаре
menu = [{"url": "home", 'name': 'Home'},
        {"url": "profile_bp.profile", 'name': 'Профиль'},
        {"url": "chats_bp.page_chats", 'name': 'Чаты'},
        {"url": "search_bp.search", 'name': 'Поиск'}
        ]

search_bp = Blueprint('search_bp', __name__, url_prefix='/search')

@search_bp.route("/", methods=["POST", "GET"])
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