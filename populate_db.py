from datetime import datetime, timezone, timedelta
from app import create_app, db
from app.models import Users, Books, followers
import sqlalchemy as sa
import sqlalchemy.orm as so
from config import Config

from faker import Faker

fake = Faker()

global_password = "class"


def get_book(product):
    with open(f"data/books/{product['file_name']}", "rb") as f:
        return f.read()


def get_image(product):
    with open(f"data/books/{product['cover_image']}", "rb") as f:
        return f.read()


class Populate:
    def __init__(self):
        self.app = create_app(Config)

        self.app.app_context().push()
        db.create_all()

    def tear_down(self):
        db.session.remove()
        db.drop_all()
        self.app.app_context().pop()

    def get_user(self, num):
        return db.session.get(Users, num)

    def init_users(self, num=4):
        users = []
        for _ in range(num):
            name = fake.first_name().lower()
            user = Users(username=name, email=f"{name}@example.com")
            user.set_password(global_password)
            users.append(user)
        user = Users(username="wade", email="wade@gmail.com")
        user.set_password(global_password)
        users.append(user)

        db.session.add_all(users)
        db.session.commit()

    def init_books(self):
        now = datetime.now(timezone.utc)
        with open("data/products.json") as data_file:
            data = eval(data_file.read())

        p1 = Books(
            book_title=data[0]["book_title"],
            author=data[0]["author"],
            publish_date=now + timedelta(seconds=1),
            cover_image=get_image(data[0]),
            book_blob=get_book(data[0]),
            author_id=self.get_user(1),
        )
        p2 = Books(
            book_title=data[1]["book_title"],
            author=data[1]["author"],
            publish_date=now + timedelta(seconds=4),
            cover_image=get_image(data[1]),
            book_blob=get_book(data[1]),
            author_id=self.get_user(2),
        )

        p3 = Books(
            book_title=data[2]["book_title"],
            author=data[2]["author"],
            publish_date=now + timedelta(seconds=3),
            cover_image=get_image(data[2]),
            book_blob=get_book(data[2]),
            author_id=self.get_user(3),
        )

        p4 = Books(
            book_title=data[3]["book_title"],
            author=data[3]["author"],
            publish_date=now + timedelta(seconds=2),
            cover_image=get_image(data[3]),
            book_blob=get_book(data[3]),
            author_id=self.get_user(4),
        )

        p5 = Books(
            book_title=data[-1]["book_title"],
            author=data[-1]["author"],
            publish_date=now + timedelta(seconds=2),
            cover_image=get_image(data[-1]),
            book_blob=get_book(data[-1]),
            author_id=self.get_user(5),
        )

        db.session.add_all([p1, p2, p3, p4, p5])
        db.session.commit()

        # setup the followers
        self.get_user(1).follow(self.get_user(2))
        self.get_user(1).follow(self.get_user(4))
        self.get_user(2).follow(self.get_user(3))
        self.get_user(3).follow(self.get_user(4))
        self.get_user(5).follow(self.get_user(1))
        self.get_user(5).follow(self.get_user(2))
        db.session.commit()

        # setup likes
        self.get_user(1).like_book(p2)
        self.get_user(1).like_book(p3)
        self.get_user(1).like_book(p4)
        self.get_user(5).like_book(p1)
        self.get_user(5).like_book(p2)
        db.session.commit()

        # setup rating
        self.get_user(2).rate_book(p1, 1)
        self.get_user(3).rate_book(p1, 1.5)
        self.get_user(4).rate_book(p1, 3)
        self.get_user(5).rate_book(p1, 1)
        db.session.commit()


def main():
    populate = Populate()
    down = input("tear down: y or n\n")

    if down == "y":
        populate.tear_down()

    populate.init_users()

    populate.init_books()

    down = input("tear down: y or n\n")

    if down == "y":
        populate.tear_down()


if __name__ == "__main__":
    main()
