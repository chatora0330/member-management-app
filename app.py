import os

from flask import Flask, redirect, url_for, flash, request
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect, CSRFError

from auth import bp as auth_bp
from csv_routes import bp as csv_bp
from database import get_db
from members import bp as members_bp
from models import User


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key"
)

csrf = CSRFProtect(app)

if app.config["SECRET_KEY"] == "dev-secret-key":
    print("⚠️ WARNING: Using development SECRET_KEY")


# --- Flask-Login 設定 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = None

# --- ユーザー読み込み ---
@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:
        user = conn.execute(
            """
            SELECT id, name, password 
            FROM users 
            WHERE id = ?
            """, 
            (user_id,)
            ).fetchone()
        if user:
            return User.from_row(user)
    return None


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("members.list_members"))
    return redirect(url_for("auth.login"))


@app.errorhandler(CSRFError)
def handle_csrf_error(_):
    flash("セッションが無効になりました。もう一度操作してください。", "danger")

    if request.referrer:
        return redirect(request.referrer)

    return redirect(url_for("auth.login"))


app.register_blueprint(auth_bp)
app.register_blueprint(members_bp)
app.register_blueprint(csv_bp)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
