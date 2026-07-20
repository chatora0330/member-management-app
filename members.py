from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    abort,
    flash,
)

from flask_login import login_required
from database import get_db
from utils import get_yomi, format_phone
from datetime import datetime
from config import PER_PAGE

bp = Blueprint("members", __name__, url_prefix="/members")

# --- CRUD ---

@bp.route("/add", methods=["GET"])
@login_required
def add_form():
    return render_template("add.html")

@bp.route("/add", methods=["POST"])
@login_required
def add():
    name = request.form.get("name","").strip()
    if not name:
        flash("名前を入力してください", "warning")
        return redirect(url_for("members.add_form"))

    yomi = get_yomi(name)
    
    phone = format_phone(request.form.get("phone", "").strip())
    
    email = request.form.get("email", "").strip().lower()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO members 
            (name, yomi, phone, email, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, yomi, phone, email, now, now)
        )

    flash("登録しました", "success")
    return redirect(url_for("members.list_members"))

@bp.route("/")
@login_required
def list_members():
    query = request.args.get("query", "", type=str)
    page = request.args.get("page", 1, type=int)
    
    page = max(page, 1)
    
    sort = request.args.get("sort", "name").lower()
    order = request.args.get("order", "asc").lower()
    
    offset = (page - 1) * PER_PAGE
    
    order = "DESC" if order == "desc" else "ASC"

    if sort == "name":
        order_by = f"yomi {order}, id {order}"
    elif sort == "id":
        order_by = f"id {order}"
    else:
        order_by = "yomi ASC, id ASC"
        
    with get_db() as conn:
        if query:
            # 検索あり
            members = conn.execute(
                f"""
                SELECT id, name, yomi, phone, email, created_at, updated_at
                FROM members
                WHERE name LIKE ? OR yomi LIKE ? OR phone LIKE ? OR email LIKE ? 
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", PER_PAGE, offset)
            ).fetchall()

            total = conn.execute(
                """
                SELECT COUNT(*) 
                FROM members 
                WHERE name LIKE ? OR yomi LIKE ? OR phone LIKE ? OR email LIKE ?
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")
            ).fetchone()[0]

        else:
            # 検索なし
            members = conn.execute(
                f"""
                SELECT id, name, yomi, phone, email, created_at, updated_at
                FROM members
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                (PER_PAGE, offset)
            ).fetchall()

            total = conn.execute(
                """
                SELECT COUNT(*) 
                FROM members
                """
                ).fetchone()[0]

    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    return render_template(
        "list.html",
        members=members,
        page=page,
        total_pages=total_pages,
        total=total,
        query=query,
        sort=sort,
        order=order
    )


@bp.route("/edit/<int:member_id>")
@login_required
def edit(member_id):
    with get_db() as conn:
        member = conn.execute(
            """
            SELECT
                id, 
                name, 
                yomi,
                phone,
                email,
                created_at,
                updated_at
            FROM members 
            WHERE id = ?
            """, 
            (member_id,)
        ).fetchone()
        
    if member is None:
        abort(404)

    return render_template("edit.html", member=member)


@bp.route("/update/<int:member_id>", methods=["POST"])
@login_required
def update(member_id):
    new_name = request.form.get("name","").strip()
    new_yomi = request.form.get("yomi", "").strip() 
    new_phone = format_phone(request.form.get("phone", "").strip())
    new_email = request.form.get("email", "").strip().lower()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not new_name:
        flash("名前を入力してください", "warning")
        return redirect(url_for("members.edit", member_id=member_id))
    
    if not new_yomi:
        new_yomi = get_yomi(new_name)
    
    with get_db() as conn:
        member = conn.execute(
            """
            SELECT id 
            FROM members 
            WHERE id = ?
            """,
            (member_id,)
        ).fetchone()

        if member is None:
            abort(404)
        
        conn.execute(
            """
            UPDATE members 
            SET 
                name = ?, 
                yomi = ?,
                phone = ?,
                email = ?,
                updated_at = ? 
            WHERE id = ?
            """,
            (new_name, new_yomi, new_phone, new_email, now, member_id)
        )
    
    flash("更新しました", "success")
    return redirect(url_for("members.list_members"))


@bp.route("/delete/<int:member_id>", methods=["POST"])
@login_required
def delete(member_id):
    with get_db() as conn:
        member = conn.execute(
            """
            SELECT id 
            FROM members 
            WHERE id = ?
            """,
            (member_id,)
        ).fetchone()

        if member is None:
            abort(404)
        
        conn.execute(
            """
            DELETE 
            FROM members 
            WHERE id = ?
            """, 
            (member_id,)
        )
    flash("削除しました", "warning")
    return redirect(url_for("members.list_members"))
