from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from .db import db
from app import login


# Cache model to store cache data in the 'cache_db'
class CacheEntry(db.Model):
    __bind_key__ = "cache_db"  # This binds the model to the 'cache_db'
    id = db.Column(db.Integer, primary_key=True)  # random id
    key = db.Column(db.String(255), nullable=False)  # Cache key
    value = db.Column(db.PickleType, nullable=False)  # Cache value (pickled)
    expiration = db.Column(db.Integer, nullable=False)  # Expiration time

    user_id = db.Column(db.Integer, nullable=False)


followers = sa.Table(
    "followers",
    db.metadata,
    sa.Column("follower_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("followed_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
)


class Users(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))

    books: so.WriteOnlyMapped["Books"] = so.relationship(back_populates="author_id")

    following: so.WriteOnlyMapped["Users"] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates="followers",
    )
    followers: so.WriteOnlyMapped["Users"] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates="following",
    )

    liked = db.relationship(
        "BookLike", foreign_keys="BookLike.user_id", backref="user", lazy="dynamic"
    )

    rated = db.relationship(
        "BookRated", foreign_keys="BookRated.user_id", backref="user", lazy="dynamic"
    )

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    def rate_book(self, book_id, rating):
        book = db.session.scalar(sa.select(Books).where(Books.id == book_id))
        if not self.has_rated_book(book):
            rate = BookRated(user_id=self.id, book_id=book.id, rating=rating)
            db.session.add(rate)
            book.update_rating()
        else:
            query = sa.select(BookRated).where(
                BookRated.user_id == self.id, BookRated.book_id == book.id
            )
            rate = db.session.scalar(query)
            rate.rating = rating
            db.session.commit()
            book.update_rating()

    def has_rated_book(self, book):
        return (
            BookRated.query.filter(
                BookRated.user_id == self.id, BookRated.book_id == book.id
            ).count()
            > 0
        )

    def like_book(self, book):
        if not self.has_liked_book(book):
            like = BookLike(user_id=self.id, book_id=book.id)
            db.session.add(like)

    def unlike_book(self, book):
        if self.has_liked_book(book):
            BookLike.query.filter_by(user_id=self.id, book_id=book.id).delete()

    def has_liked_book(self, book):
        return (
            BookLike.query.filter(
                BookLike.user_id == self.id, BookLike.book_id == book.id
            ).count()
            > 0
        )

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(Users.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery()
        )
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery()
        )
        return db.session.scalar(query)

    def following_books(self):
        Author = so.aliased(Users)
        Follower = so.aliased(Users)
        return (
            sa.select(Books)
            .join(Books.author_id.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(
                Follower.id == self.id,
            )
            .group_by(Books)
            .order_by(Books.publish_date.desc())
        )


@login.user_loader
def load_user(id):
    return db.session.get(Users, int(id))


class BookLike(db.Model):
    __tablename__ = "book_like"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))


class BookRated(db.Model):
    __tablename__ = "book_rated"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))
    rating = db.Column(db.Float)


class Books(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    book_title: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True)
    author: so.Mapped[str] = so.mapped_column(sa.String(64))
    isbn: so.Mapped[Optional[int]] = so.mapped_column()
    publish_date: so.Mapped[Optional[datetime]] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )

    cover_image = so.mapped_column(sa.BLOB)
    book_blob = so.mapped_column(sa.BLOB)

    likes = db.relationship("BookLike", backref="books", lazy="dynamic")

    rated = db.relationship("BookRated", backref="books", lazy="dynamic")

    rating: so.Mapped[Optional[float]] = so.mapped_column(default=0)

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Users.id), index=True)

    author_id: so.Mapped[Users] = so.relationship(back_populates="books")

    def update_rating(self):
        self.rating = (
            round(
                db.session.query(db.func.avg(BookRated.rating))
                .filter(BookRated.book_id == self.id)
                .scalar()
                * 2
            )
            / 2
        )
        db.session.commit()
