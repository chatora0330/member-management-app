from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
)

from flask_login import (
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from database import get_db

from models import User


bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
    )

# --- サインアップ ---
@bp.route("/signup", methods=["GET", "POST"])
def signup():
    # ログイン済みなら名簿一覧へ
    if current_user.is_authenticated:
        return redirect(url_for("members.list_members"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        
        if not name or not password:
            flash("ユーザー名とパスワードを入力してください", "warning")
            return render_template("signup.html")
        
        password = generate_password_hash(password)

        with get_db() as conn:
            exists = conn.execute(
                """
                SELECT id 
                FROM users 
                WHERE name=?
                """,
            (name,)
            ).fetchone()
            
            if exists:
                flash("そのユーザー名は既に使用されています", "warning")
                return render_template("signup.html")
            
            conn.execute(
                """
                INSERT INTO users (name, password) 
                VALUES (?, ?)
                """, 
                (name, password)
            )

        flash("ユーザーを登録しました。ログインしてください", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")

# --- ログイン ---
@bp.route("/login", methods=["GET", "POST"])
def login():
    # 既にログイン済みなら名簿一覧へ
    if current_user.is_authenticated:
        return redirect(url_for("members.list_members"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        
        if not name or not password:
            flash("ユーザー名とパスワードを入力してください", "warning")
            return render_template("login.html")

        with get_db() as conn:
            user = conn.execute(
                """
                SELECT id, name, password
                FROM users 
                WHERE name = ?
                """, 
                (name,)
                ).fetchone()

        if user and check_password_hash(user["password"], password):
            login_user(User.from_row(user))
            return redirect(url_for("members.list_members"))
        else:
            flash("ユーザー名またはパスワードが違います", "danger")
            return render_template("login.html")

    return render_template("login.html")

# --- ログアウト ---
@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
