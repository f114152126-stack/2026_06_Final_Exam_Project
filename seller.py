from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from models import db, User, Food, Reservation, Comment

seller_bp = Blueprint(
    "seller",
    __name__
)


# ==========================
# 權限檢查
# ==========================
def seller_required():

    if "user_id" not in session:
        return False

    if session.get("role") != "seller":
        return False

    return True


# ==========================
# 商家首頁
# ==========================
@seller_bp.route("/dashboard")
def dashboard():

    if not seller_required():
        return redirect(url_for("login"))

    user = User.query.get(
        session["user_id"]
    )

    foods = Food.query.filter_by(
        seller_id=session["user_id"]
    ).all()

    return render_template(
        "seller_dashboard.html",
        foods=foods,
        user=user
    )


# ==========================
# 新增剩食
# ==========================
@seller_bp.route(
    "/add_food",
    methods=["GET", "POST"]
)
def add_food():

    if not seller_required():
        return redirect(url_for("login"))
    
    user = User.query.get(
        session["user_id"]
    )
    if not user.city or not user.district:
        flash("請先設定地區")
        return redirect(url_for("set_area"))
    
    if request.method == "POST":

        food = Food(
            name=request.form["name"],
            description=request.form["description"],
            quantity=int(
                request.form["quantity"]
            ),
            pickup_time=request.form[
                "pickup_time"
            ],
            seller_id=session["user_id"]
        )

        db.session.add(food)
        db.session.commit()

        flash("新增成功")

        return redirect(
            url_for("seller.dashboard")
        )

    return render_template(
        "add_food.html"
    )


# ==========================
# 編輯剩食
# ==========================
@seller_bp.route(
    "/edit_food/<int:food_id>",
    methods=["GET", "POST"]
)
def edit_food(food_id):

    if not seller_required():
        return redirect(url_for("login"))

    food = Food.query.get_or_404(
        food_id
    )

    if request.method == "POST":

        food.name = request.form["name"]
        food.description = request.form[
            "description"
        ]

        food.quantity = int(
            request.form["quantity"]
        )

        food.pickup_time = request.form[
            "pickup_time"
        ]

        db.session.commit()

        flash("更新成功")

        return redirect(
            url_for("seller.dashboard")
        )

    return render_template(
        "edit_food.html",
        food=food
    )


# ==========================
# 刪除剩食
# ==========================
@seller_bp.route(
    "/delete_food/<int:food_id>"
)
def delete_food(food_id):

    if not seller_required():
        return redirect(url_for("login"))

    food = Food.query.filter_by(
        id=food_id,
        seller_id=session["user_id"]
    ).first()

    if not food:

        flash("找不到該食品")

        return redirect(
            url_for("seller.dashboard")
        )

    active_reservation = Reservation.query.filter_by(
        food_id=food.id,
        status="已預約"
    ).first()

    if active_reservation:

        flash("該食品已有預約，無法刪除")

        return redirect(
            url_for("seller.dashboard")
        )

    db.session.delete(food)
    db.session.commit()

    flash("刪除成功")

    return redirect(
        url_for("seller.dashboard")
    )

# ==========================
# 查看預約名單
# ==========================
@seller_bp.route(
    "/reservations"
)
def reservations():

    if not seller_required():
        return redirect(url_for("login"))

    foods = Food.query.filter_by(
        seller_id=session["user_id"]
    ).all()

    food_ids = [
        food.id for food in foods
    ]

    reservation_list = (
        Reservation.query
        .filter(
            Reservation.food_id.in_(
                food_ids
            ),
            Reservation.status == "已預約"
        )
        .all()
    )

    return render_template(
        "reservation_list.html",
        reservations=reservation_list
    )

# ==========================
# 查看評論名單
# ==========================
@seller_bp.route("/comments")
def comments():
    if not seller_required():
        return redirect(url_for("login"))

    # 1. 撈出屬於該商家的所有已完成/已評論的預約紀錄
    # 這裡可以根據你原有的邏輯篩選，範例是以 comments_status == "已評論" 為主
    seller_id = session.get("user_id")
    
    # 先撈出該商家上架的所有食品 ID
    seller_food_ids = [f.id for f in Food.query.filter_by(seller_id=seller_id).all()]
    
    # 根據這些食品 ID 找出對應的預約紀錄
    reservations = Reservation.query.filter(
        Reservation.food_id.in_(seller_food_ids),
        Reservation.user_id == seller_id,
        Reservation.comments_status == "已評論"
    ).all()

    # 2. 核心：遍歷每筆預約，把查到的整個 Comment 物件綁定到 r.comment
    for r in reservations:
        r.comment = Comment.query.filter_by(reservation_id=r.id).first()

    return render_template(
        "comments.html",  # 請確保與你實際的 HTML 檔名一致
        reservations=reservations
    )

# ==========================
# 完成預約
# ==========================
@seller_bp.route(
    "/finish_reservation/<int:reservation_id>"
)
def finish_reservation(reservation_id):

    if not seller_required():
        return redirect(url_for("login"))

    reservation = Reservation.query.get_or_404(
        reservation_id
    )

    food = Food.query.get_or_404(
        reservation.food_id
    )

    if food.quantity < 1:
        db.session.delete(food)

    reservation.status = "已完成"

    # db.session.delete(reservation)
    db.session.commit()

    flash("預約已完成")

    return redirect(
        url_for("seller.reservations")
    )
