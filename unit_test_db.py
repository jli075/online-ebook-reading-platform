from datetime import datetime, timezone, timedelta
import unittest
from app import create_app, db
from app.models import Users, Books
from config import Config
import sqlalchemy as sa


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


def get_book(product):
    with open(f"data/books/{product['file_name']}", "rb") as f:
        return f.read()


def get_image(product):
    with open(f"data/books/{product['cover_image']}", "rb") as f:
        return f.read()


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = Users(username="susan", email="susan@example.com")
        u.set_password("cat")
        self.assertFalse(u.check_password("dog"))
        self.assertTrue(u.check_password("cat"))

    def test_avatar(self):
        u = Users(username="john", email="john@example.com")
        self.assertEqual(
            u.avatar(128),
            (
                "https://www.gravatar.com/avatar/"
                "d4c74594d841139328695756648b6bd6"
                "?d=identicon&s=128"
            ),
        )

    def test_follow(self):
        u1 = Users(username="john", email="john@example.com")
        u2 = Users(username="susan", email="susan@example.com")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        following = db.session.scalars(u1.following.select()).all()
        followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 1)
        self.assertEqual(u2.followers_count(), 1)
        u1_following = db.session.scalars(u1.following.select()).all()
        u2_followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(u1_following[0].username, "susan")
        self.assertEqual(u2_followers[0].username, "john")

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

    def test_follow_posts(self):
        # create four users
        u1 = Users(username="john", email="john@example.com")
        u1.set_password("class")

        u2 = Users(username="susan", email="susan@example.com")
        u2.set_password("class")

        u3 = Users(username="mary", email="mary@example.com")
        u3.set_password("class")

        u4 = Users(username="david", email="david@example.com")
        u4.set_password("class")

        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.now(timezone.utc)
        with open("data/products.json") as data_file:
            data = eval(data_file.read())

        p1 = Books(
            book_title=data[0]["book_title"],
            author=data[0]["author"],
            publish_date=now + timedelta(seconds=1),
            cover_image=get_image(data[0]),
            book_blob=get_book(data[0]),
            author_id=u1,
        )
        p2 = Books(
            book_title=data[1]["book_title"],
            author=data[1]["author"],
            publish_date=now + timedelta(seconds=4),
            cover_image=get_image(data[1]),
            book_blob=get_book(data[1]),
            author_id=u2,
        )

        p3 = Books(
            book_title=data[2]["book_title"],
            author=data[2]["author"],
            publish_date=now + timedelta(seconds=3),
            cover_image=get_image(data[2]),
            book_blob=get_book(data[2]),
            author_id=u3,
        )

        p4 = Books(
            book_title=data[3]["book_title"],
            author=data[3]["author"],
            publish_date=now + timedelta(seconds=2),
            cover_image=get_image(data[3]),
            book_blob=get_book(data[3]),
            author_id=u4,
        )

        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u3)
        u3.follow(u4)
        db.session.commit()

        # check the following posts of each user
        f1 = db.session.scalars(u1.following_books()).all()
        f2 = db.session.scalars(u2.following_books()).all()
        f3 = db.session.scalars(u3.following_books()).all()
        f4 = db.session.scalars(u4.following_books()).all()
        self.assertEqual(f1, [p2, p4])
        self.assertEqual(f2, [p3])
        self.assertEqual(f3, [p4])
        self.assertEqual(f4, [])

    def test_cover_image(self):
        # create four users
        u1 = Users(username="john", email="john@example.com")
        u1.set_password("class")

        u2 = Users(username="susan", email="susan@example.com")
        u2.set_password("class")

        u3 = Users(username="mary", email="mary@example.com")
        u3.set_password("class")

        u4 = Users(username="david", email="david@example.com")
        u4.set_password("class")

        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.now(timezone.utc)
        with open("data/products.json") as data_file:
            data = eval(data_file.read())

        p1 = Books(
            book_title=data[0]["book_title"],
            author=data[0]["author"],
            publish_date=now + timedelta(seconds=1),
            cover_image=get_image(data[0]),
            book_blob=get_book(data[0]),
            author_id=u1,
        )

        p2 = Books(
            book_title=data[1]["book_title"],
            author=data[1]["author"],
            publish_date=now + timedelta(seconds=4),
            cover_image=get_image(data[1]),
            book_blob=get_book(data[1]),
            author_id=u2,
        )

        p3 = Books(
            book_title=data[2]["book_title"],
            author=data[2]["author"],
            publish_date=now + timedelta(seconds=3),
            cover_image=get_image(data[2]),
            book_blob=get_book(data[2]),
            author_id=u3,
        )

        p4 = Books(
            book_title=data[3]["book_title"],
            author=data[3]["author"],
            publish_date=now + timedelta(seconds=2),
            cover_image=get_image(data[3]),
            book_blob=get_book(data[3]),
            author_id=u4,
        )

        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        query = db.first_or_404(sa.select(Books.cover_image).where(Books.id == 1))
        # print(query)


if __name__ == "__main__":
    unittest.main(verbosity=2)
