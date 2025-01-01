"""General page routes."""

from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    jsonify,
    g,
)
from flask import render_template

import sqlalchemy as sa
from sqlalchemy import func
from flask_login import current_user, login_required
from app import db
from app.models import Users, Books, BookLike, BookRated
from app.forms import EmptyForm, SearchForm


# Blueprint Configuration
home_blueprint = Blueprint(
    "home_blueprint", __name__, template_folder="templates", static_folder="static"
)


@home_blueprint.before_app_request
def before_request():
    g.search_form = SearchForm()


@home_blueprint.route("/", methods=["GET"])
def home():
    """
    Serve `Home` page template.
    """
    products = db.session.scalars(sa.select(Books)).all()
    return render_template(
        "index.jinja2",
        title="Home",
        subtitle="Book Reading Platform",
        template="home-template",
        products=products,
    )


@home_blueprint.route("/search")
def search():
    products = []
    search_query = "Results For: "
    if g.search_form.validate():
        products = (
            Books.query.filter(Books.book_title.like(f"%{g.search_form.q.data}%"))
            .order_by(Books.book_title)
            .all()
        )
        search_query += g.search_form.q.data
    return render_template(
        "index.jinja2",
        title="Search",
        subtitle=search_query,
        template="home-template",
        products=products,
    )


@home_blueprint.route("/popular", methods=["GET"])
def popular():
    """
    Serve `Popular` page template.
    """
    # highest_rated_books = db.session.query(Books).outerjoin(BookRated).group_by(Books.id).order_by(
    #     Books.rating.desc().nullslast()).all()

    # # Query for books with likes, including those with no likes
    # most_liked_books = db.session.query(Books).outerjoin(BookLike).group_by(Books.id).order_by(
    #     func.count(BookLike.id).desc()).all()

    # Combine both lists of books and sort by both rating and likes, then alphabetically by title
    # set(highest_rated_books + most_liked_books)
    products = sorted(
        set(
            db.session.query(Books)
            .outerjoin(BookRated)
            .group_by(Books.id)
            .order_by(Books.rating.desc().nullslast())
            .all()
            + db.session.query(Books)
            .outerjoin(BookLike)
            .group_by(Books.id)
            .order_by(func.count(BookLike.id).desc())
            .all()
        ),
        key=lambda x: (
            (x.rating if x.rating is not None else 0),
            db.session.query(func.count(BookLike.id))
            .filter(BookLike.book_id == x.id)
            .scalar()
            or 0,
            x.book_title.lower(),
        ),
        reverse=True,
    )

    return render_template(
        "index.jinja2",
        title="Most Popular",
        subtitle="Top books",
        template="home-template page",
        products=products,
    )



@home_blueprint.route("/cover/<id>", methods=["GET", "POST"])
def cover_data(id):
    return db.first_or_404(sa.select(Books.cover_image).where(Books.id == id))


@home_blueprint.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(Users).where(Users.username == username))
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for("home_blueprint.index"))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(
                url_for("profile_blueprint.user_profile", username=username)
            )
        current_user.follow(user)
        db.session.commit()
        flash(f"You are following {username}!")
        return redirect(url_for("profile_blueprint.user_profile", username=username))
    else:
        return redirect(url_for("home_blueprint.index"))


@home_blueprint.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(Users).where(Users.username == username))
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for("home_blueprint.index"))
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(
                url_for("profile_blueprint.user_profile", username=username)
            )
        current_user.unfollow(user)
        db.session.commit()
        flash(f"You are not following {username}.")
        return redirect(url_for("profile_blueprint.user_profile", username=username))
    else:
        return redirect(url_for("home_blueprint.index"))


@home_blueprint.route("/like/<int:book_id>/<action>", methods=["POST"])
@login_required
def like_action(book_id, action):
    book = Books.query.filter_by(id=book_id).first_or_404()

    success = False

    if action == "like":
        current_user.like_book(book)
        db.session.commit()
        success = True
    elif action == "unlike":
        current_user.unlike_book(book)
        db.session.commit()
        success = True

    # Return a JSON response indicating success or failure
    return jsonify({"success": success})
