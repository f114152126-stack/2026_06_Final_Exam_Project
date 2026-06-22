from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from models import (
    db,
    User,
    Food,
    Reservation,
    Comment,
    Promotion
)

user_bp = Blueprint(
    "user",
    __name__
)

from sqlalchemy.orm import joinedload
from datetime import datetime

# ==========================
# 權限檢查
# ==========================
def user_required():

    if "user_id" not in session:
        return False

    if session.get("role") != "user":
        return False

    return True

# ==========================
# 用戶首頁
# ==========================
@user_bp.route("/dashboard")
def dashboard():

    if not user_required():
        return redirect(url_for("login"))
    
    user = User.query.get(
        session["user_id"]
    )
    
    seller_list = User.query.filter_by(
        city=user.city,
        district=user.district,
        role="seller"
    ).all()

    seller_ids = [
        seller.id
        for seller in seller_list
    ]

    food_list = Food.query.filter(
        Food.seller_id.in_(seller_ids)
    ).all()

    seller_ids = [
        seller.id
        for seller in User.query.filter_by(
            city=user.city,
            district=user.district,
            role="seller"
        ).all()
    ]

    promotions = Promotion.query.filter(
        Promotion.seller_id.in_(seller_ids),
        Promotion.end_date >= datetime.now()
    ).all()

    return render_template(
        "user_dashboard.html",
        foods=food_list,
        user=user,
        promotions=promotions
    )

# ==========================
# 預約剩食
# ==========================
@user_bp.route(
    "/reserve/<int:food_id>"
)
def reserve(food_id):

    if not user_required():
        return redirect(url_for("login"))

    food = Food.query.get_or_404(
        food_id
    )

    if food.quantity <= 0:

        flash("已無剩餘數量")

        return redirect(
            url_for("user.dashboard")
        )

    exist = Reservation.query.filter_by(
        food_id=food_id,
        food_name=food.name,
        user_id=session["user_id"],
        user_name=session["username"],
        status="已預約"
    ).first()

    if food.quantity > 0:
        food.quantity -= 1
    else:
        flash("已無剩餘數量")
        return redirect(
            url_for("user.dashboard")
        )

    if exist:
        exist.quantity += 1
    
    else:
        reservation = Reservation(
            food_id=food_id,
            food_name=food.name,
            user_id=session["user_id"],
            user_name=session["username"]
        )
        
        db.session.add(reservation)

    db.session.commit()

    flash("預約成功")

    return redirect(
        url_for("user.dashboard")
    )

# ==========================
# 取消預約
# ==========================
@user_bp.route(
    "/cancel_reservation/<int:reservation_id>"
)
def cancel_reservation(reservation_id):

    if not user_required():
        return redirect(url_for("login"))

    reservation = Reservation.query.get_or_404(
        reservation_id
    )

    food = Food.query.get_or_404(
        reservation.food_id
    )

    food.quantity += 1

    if reservation.quantity > 1:
        reservation.quantity -= 1
    else:
        db.session.delete(reservation)
        
    db.session.commit()

    flash("預約已取消")

    return redirect(
        url_for("user.my_reservations")
    )

# ==========================
# 評論
# ==========================
@user_bp.route(
    "/comment/<int:reservation_id>",
    methods=["POST"]
)
def comment(reservation_id):

    if not user_required():
        return redirect(url_for("login"))

    reservation = Reservation.query.get_or_404(
        reservation_id
    )

    content = request.form.get(
        "content"
    )

    if not content:

        flash("請輸入評論內容")

        return redirect(
            url_for("user.my_comments")
        )

    comment = Comment(
        reservation_id=reservation_id,
        user_id=reservation.user_id,
        food_id=reservation.food_id,
        content=content
    )

    reservation.comments_status = "已評論"

    db.session.add(comment)
    db.session.commit()

    flash("評論成功")

    return redirect(
        url_for("user.my_comments")
    )

# ==========================
# 我的預約
# ==========================
@user_bp.route(
    "/my_reservations"
)
def my_reservations():

    if not user_required():
        return redirect(url_for("login"))

    reservations = Reservation.query.filter_by(
        user_id=session["user_id"],
        status="已預約"
    ).all()

    return render_template(
        "my_reservation.html",
        reservations=reservations
    )

# ==========================
# 我的評論 
# ==========================
@user_bp.route("/my_comments")
def my_comments():
    if not user_required():
        return redirect(url_for("login"))

    # 使用 joinedload("comment") 或根據你的對應名稱載入。
    # 這裡我們用最穩健的外連結方式，將 Comment 物件直接綁在 reservation 上
    reservations = Reservation.query.filter_by(
        user_id=session["user_id"],
        status="已完成"
    ).all()

    # 尋找每筆預約對應的 comment 物件，並將其賦值給 r.comment
    for r in reservations:
        r.comment = Comment.query.filter_by(reservation_id=r.id).first()

    return render_template(
        "my_comments.html",
        reservations=reservations
    )

# ==========================
# 編輯評論 
# ==========================
@user_bp.route("/edit_comment/<int:reservation_id>", methods=["POST"])
def edit_comment(reservation_id):
    if not user_required():
        return redirect(url_for("login"))

    # 找出該筆預約對應的評論（這裡假設你的 Comment 欄位是 reservation_id）
    comment = Comment.query.filter_by(
        reservation_id = reservation_id
    ).first_or_404()
    
    content = request.form.get("content")
    if not content:
        flash("評論內容不能為空")
        return redirect(url_for("user.my_comments"))

    # 更新評論內容
    comment.content = content
    db.session.commit()
    
    flash("評論修改成功")
    return redirect(url_for("user.my_comments"))

# ==========================
# 顯示最新活動
# ==========================
