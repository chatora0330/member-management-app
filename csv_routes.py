import csv
import io

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    Response,
)

from flask_login import login_required
from database import get_db
from utils import get_yomi, format_phone
from datetime import datetime


bp = Blueprint(
    "csv",
    __name__, 
    url_prefix="/csv"
    )

# --- CSV ---

@bp.route("/export")
@login_required
def export_csv():

    with get_db() as conn:
        members = conn.execute("""
            SELECT
                id,
                name,
                yomi,
                phone,
                email,
                created_at,
                updated_at
            FROM members
            ORDER BY yomi ASC, id ASC
        """).fetchall()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "名前",
        "読み仮名",
        "電話番号",
        "メールアドレス",
        "登録日時",
        "更新日時"
    ])

    for member in members:
        writer.writerow([
            member["id"],
            member["name"],
            member["yomi"],
            member["phone"],
            member["email"],
            member["created_at"],
            member["updated_at"]
        ])

    response = Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=members.csv"
    )

    return response


@bp.route("/import", methods=["POST"])
@login_required
def import_csv():

    file = request.files.get("csv_file")

    if not file or file.filename == "":
        flash("CSVファイルを選択してください", "warning")
        return redirect(url_for("members.list_members"))

    inserted = 0
    error_count = 0
    errors = []

    try:
        stream = io.StringIO(
            file.stream.read().decode("utf-8-sig")
        )

        reader = csv.reader(stream)

        # ヘッダーを読み飛ばす
        next(reader, None)

        with get_db() as conn:

            for line_no, row in enumerate(reader, start=2):

                try:

                    # 空行
                    if not row:
                        continue

                    # エクスポートしたCSV
                    if len(row) >= 7:
                        name = row[1].strip()
                        phone = row[3].strip()
                        email = row[4].strip()

                    # テンプレートCSV
                    elif len(row) >= 3:
                        name = row[0].strip()

                        phone = (
                            row[1]
                            .replace(" ", "")
                            .replace("　", "")
                            .strip()
                        )

                        email = row[2].strip().lower()                        
                        
                    else:
                        error_count += 1
                        errors.append(f"{line_no}行目：CSVの形式が正しくありません")
                        continue

                    # 名前が空
                    if not name:
                        error_count += 1
                        errors.append(f"{line_no}行目：名前が空です")
                        continue
                    
                    phone = format_phone(phone) 

                    yomi = get_yomi(name)

                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    conn.execute(
                        """
                        INSERT INTO members
                        (
                            name,
                            yomi,
                            phone,
                            email,
                            created_at,
                            updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            name,
                            yomi,
                            phone,
                            email,
                            now,
                            now
                        )
                    )

                    inserted += 1

                except Exception:
                    error_count += 1
                    errors.append(
                        f"{line_no}行目：登録できませんでした"
                    )
                    continue

        message = (
            f"インポート完了\n"
            f"登録：{inserted}件\n"
            f"エラー：{error_count}件"
        )

        if errors:
            message += "\n\n【エラー一覧】\n"
            message += "\n".join(errors)

        if errors:
            flash(message, "warning")
        else:
            flash(message, "success")

    except Exception:
        flash("CSVの読み込みに失敗しました", "danger")

    return redirect(url_for("members.list_members"))


@bp.route("/template")
@login_required
def download_template():

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "名前",
        "電話番号",
        "メールアドレス"
    ])

    response = Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8"
    )

    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=template.csv"

    return response

