from typing import Any, List

from flask_login import UserMixin
from sqlalchemy.orm import RelationshipProperty

from market import bcrypt, db, login_manager


@login_manager.user_loader
def load_user(user_id: str) -> "User":
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    budget = db.Column(db.Integer(), nullable=False, default=1000)
    items = db.relationship("Item", backref="owned_user", lazy=True)

    @property
    def prettier_budget(self) -> str:
        if len(str(self.budget)) >= 4:
            return f"{str(self.budget)[:-3]},{str(self.budget)[-3:]}$"
        else:
            return f"{self.budget}$"

    @property
    def password(self) -> str:
        return self.password

    @password.setter
    def password(self, plain_text_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode(
            "utf-8"
        )

    def check_password_correction(self, attempted_password: str) -> str:
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

    def can_purchase(self, item_obj: "Item") -> bool:
        return self.budget >= item_obj.price

    def can_sell(self, item_obj: "Item") -> bool:
        return item_obj in list(self.items)


class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    owner = db.Column(db.Integer(), db.ForeignKey("user.id"))

    def __repr__(self) -> str:
        return f"Item {self.name}"

    def buy(self, user: User) -> None:
        self.owner = user.id
        user.budget -= self.price
        db.session.commit()

    def sell(self, user: User) -> None:
        self.owner = None
        user.budget += self.price
        db.session.commit()
