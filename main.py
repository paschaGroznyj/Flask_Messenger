from flask import render_template
from flask_login import login_required
from app_db import app
from blueprints import profile, register, login, search, chats

app.register_blueprint(profile.profile_bp)
app.register_blueprint(register.register_bp)
app.register_blueprint(login.login_bp)
app.register_blueprint(search.search_bp)
app.register_blueprint(chats.chats_bp)

#Отображение в навбаре
menu = [{"url": "home", 'name': 'Home'},
        {"url": "profile_bp.profile", 'name': 'Профиль'},
        {"url": "chats_bp.page_chats", 'name': 'Чаты'},
        {"url": "search_bp.search", 'name': 'Поиск'}
        ]

@app.route("/home")
@login_required
def home():
        return render_template("home.html", menu = menu)


if __name__ == "__main__":
        app.run(host="0.0.0.0", port = 5000, debug=True)