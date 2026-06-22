from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    __table_args__ = {
        "sqlite_autoincrement": True
    }

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )  # seller / user

    city = db.Column(
        db.String(50)
    )

    district = db.Column(
        db.String(50)
    )

    is_premium = db.Column(
    db.Boolean,
    default=False
    )


class Food(db.Model):
    __tablename__ = "foods"

    __table_args__ = {
        "sqlite_autoincrement": True
    }

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    pickup_time = db.Column(
        db.String(100),
        nullable=False
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    
    __table_args__ = {
        "sqlite_autoincrement": True
    }

    food_id = db.Column(
        db.Integer,
        db.ForeignKey("foods.id")
    )

    food_name = db.Column(
        db.String(100),
        db.ForeignKey("foods.name")
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )
    
    user_name = db.Column(
        db.String(50),
        db.ForeignKey("users.username")
    )

    quantity = db.Column(
        db.Integer,
        default=1
    )

    reserve_time = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
    status = db.Column(
        db.String(50),
        default="已預約"
    )

    comments_status = db.Column(
        db.String(50),
        default="未評論"
    )

class Comment(db.Model):
    __tablename__ = "comments"

    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey("reservations.id"),
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    food_id = db.Column(
        db.Integer,
        db.ForeignKey("foods.id"),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

class Promotion(db.Model):
    __tablename__ = "promotions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    title = db.Column(
        db.String(100),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    start_date = db.Column(
        db.DateTime,
        nullable=False
    )

    end_date = db.Column(
        db.DateTime,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
