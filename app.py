from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from models import (
    db,
    User,
    Food,
    Reservation,
    Comment,
    Promotion
)

from seller import seller_bp
from user import user_bp
from datetime import datetime

app = Flask(__name__)

app.secret_key = "foodsaver_secret_key"

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "sqlite:///database.db"

app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False

db.init_app(app)

app.register_blueprint(
    seller_bp,
    url_prefix="/seller"
)

app.register_blueprint(
    user_bp,
    url_prefix="/user"
)


@app.route("/")
def index():
    return render_template("index.html")


# ==========================
# 註冊
# ==========================
@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        exist_user = User.query.filter_by(
            username=username
        ).first()

        if exist_user:
            flash("帳號已存在")
            return redirect(
                url_for("register")
            )

        new_user = User(
            username=username,
            password=password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("註冊成功")

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ==========================
# 登入
# ==========================
@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password,
        ).first()

        if user:

            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            session["is_premium"] = user.is_premium

            if user.role == "seller":
                return redirect(
                    url_for(
                        "seller.dashboard"
                    )
                )

            else:
                return redirect(
                    url_for(
                        "user.dashboard"
                    )
                )

        flash("登入失敗")

    return render_template(
        "login.html"
    )

# ==========================
# 設定地區
# ==========================
@app.route(
    "/set_area",
    methods=["GET", "POST"]
)
def set_area():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(
        session["user_id"]
    )

    if request.method == "POST":

        user.city = request.form["city"]

        user.district = request.form[
            "district"
        ]

        db.session.commit()

        flash("地區設定成功")

        return redirect(
            url_for(f"{session['role']}.dashboard")
        )

    return render_template(
        "set_area.html",
        user=user
    )

# ==========================
# 登出
# ==========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )

# ==========================
# 建立資料庫
# ==========================
@app.before_request
def create_tables():
    db.create_all()

# ==========================
# 會員方案
# ==========================
@app.route(
    "/seller/upgrade",
    methods=["GET", "POST"]
)
def seller_upgrade():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(
        session["user_id"]
    )

    if request.method == "POST":

        user.is_premium = True

        db.session.commit()

        session["is_premium"] = True

        flash("恭喜升級 Premium 會員")

        return redirect(
            url_for("premium_dashboard")
        )

    return render_template(
        "premium/upgrade.html",
        user=user
    )

# ==========================
# Premium 主頁
# ==========================
@app.route("/seller/premium")
def premium_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(
        session["user_id"]
    )

    if not user.is_premium:

        flash("請先升級會員")

        return redirect(
            url_for("seller_upgrade")
        )

    return render_template(
        "premium/dashboard.html"
    )

# ==========================
# 剩食統計分析
# ==========================
@app.route(
    "/seller/premium/analytics"
)
def analytics():

    user = User.query.get(
        session["user_id"]
    )

    foods = Food.query.filter_by(
        seller_id=session["user_id"]
    ).all()

    food_ids = [
        food.id
        for food in foods
    ]

    food_count = [
        food.quantity
        for food in foods
    ]

    reservations = Reservation.query.filter(
        Reservation.food_id.in_(food_ids)
    ).all()

    reservation_count = [
        reservation.quantity
        for reservation in reservations
    ]
    
    food_count = sum(food_count) + sum(reservation_count)

    completed_count = Reservation.query.filter(
        Reservation.food_id.in_(food_ids),
        Reservation.status == "已完成"
    ).count()

    if food_count > 0:
        match_rate = round(
            completed_count / food_count * 100,
            1
        )
    else:
        match_rate = 0

    popular_foods = (
        db.session.query(
            Reservation.food_name,
            db.func.count(
                Reservation.id
            ).label("total")
        )
        .filter(
            Reservation.food_id.in_(
                food_ids
            ),
            Reservation.status == "已完成"
        )
        .group_by(
            Reservation.food_name
        )
        .order_by(
            db.desc("total")
        )
        .limit(5)
        .all()
    )

    comment_count = Comment.query.filter(
        Comment.food_id.in_(food_ids)
    ).count()

    if not user.is_premium:
        return redirect(
            url_for("seller_upgrade")
        )

    return render_template(
        "premium/analytics.html",
        food_count=food_count,
        reservation_count=sum(reservation_count),
        completed_count=completed_count,
        comment_count=comment_count,
        match_rate=match_rate,
        popular_foods=popular_foods
    )

# ==========================
# 每月營運報表
# ==========================
@app.route(
    "/seller/premium/reports"
)
def reports():

    user = User.query.get(
        session["user_id"]
    )

    if not user.is_premium:
        return redirect(
            url_for("seller_upgrade")
        )
    
    foods = Food.query.filter_by(
        seller_id=session["user_id"]
    ).all()

    food_ids = [
        food.id
        for food in foods
    ]

    today = datetime.now()

    current_year = today.year
    current_month = today.month

    monthly_reservations = Reservation.query.filter(
        Reservation.food_id.in_(food_ids),
        db.extract(
            "year",
            Reservation.reserve_time
        ) == current_year,
        db.extract(
            "month",
            Reservation.reserve_time
        ) == current_month
    ).all()

    reservation_count = len(
        monthly_reservations
    )

    completed_count = len([
        r for r in monthly_reservations
        if r.status == "已完成"
    ])

    if reservation_count:
        complete_rate = round(
            completed_count /
            reservation_count * 100,
            1
        )
    else:
        complete_rate = 0
    
    comment_count = Comment.query.filter(
        Comment.food_id.in_(food_ids)
    ).count()

    if completed_count:
        comment_rate = round(
            comment_count /
            completed_count * 100,
            1
        )
    else:
        comment_rate = 0

    saved_food_count = sum(
        r.quantity
        for r in monthly_reservations
        if r.status == "已完成"
    )

    return render_template(
        "premium/reports.html",
        current_year=current_year,
        current_month=current_month,
        reservation_count=reservation_count,
        completed_count=completed_count,
        complete_rate=complete_rate,
        comment_count=comment_count,
        comment_rate=comment_rate,
        saved_food_count=saved_food_count
    )

# ==========================
# 活動推廣
# ==========================
@app.route(
    "/seller/premium/promotion",
    methods=["GET", "POST"]
)
def promotion():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(
        session["user_id"]
    )

    if not user.is_premium:
        return redirect(
            url_for("seller_upgrade")
        )

    if request.method == "POST":

        start_date_str = request.form.get(
            "start_date"
        )

        end_date_str = request.form.get(
            "end_date"
        )

        start_date = datetime.strptime(
            start_date_str,
            "%Y-%m-%dT%H:%M"
        )

        end_date = datetime.strptime(
            end_date_str,
            "%Y-%m-%dT%H:%M"
        )

        if start_date >= end_date:

            flash(
                "開始日期不可晚於或等於結束日期"
            )

            return redirect(
                url_for("promotion")
            )

        new_promotion = Promotion(
            seller_id=user.id,
            title=request.form["title"],
            content=request.form["content"],
            start_date=start_date,
            end_date=end_date
        )

        db.session.add(
            new_promotion
        )

        db.session.commit()

        flash("活動發布成功")

        return redirect(
            url_for("promotion")
        )

    promotions = Promotion.query.filter_by(
        seller_id=user.id
    ).order_by(
        Promotion.id.desc()
    ).all()

    return render_template(
        "premium/promotion.html",
        promotions=promotions,
        today=datetime.now()
    )

# ==========================
# 結束活動
# ==========================
@app.route(
    "/seller/premium/delete_promotion/<int:promotion_id>"
)
def delete_promotion(promotion_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    promotion = Promotion.query.get_or_404(
        promotion_id
    )

    if promotion.seller_id != session["user_id"]:

        flash("無權限")

        return redirect(
            url_for("promotion")
        )

    db.session.delete(
        promotion
    )

    db.session.commit()

    flash("活動已結束")

    return redirect(
        url_for("promotion")
    )

if __name__ == "__main__":

    app.run(
        debug=True
    )