"""Product pages."""

from flask import Blueprint
from flask import render_template, request, jsonify
from flask_login import current_user, login_required

from app.models import Books, BookRated, CacheEntry
from app.db import db
from app import cache
from app.forms import RatingForm

import sqlalchemy as sa

# Blueprint Configuration
product_blueprint = Blueprint(
    "product_blueprint", __name__, template_folder="templates", static_folder="static"
)


@product_blueprint.route("/products/<int:product_id>/", methods=["GET"])
def product_page(product_id: int):
    """
    Product detail page for a given product ID.

    :params int product_id: Unique product ID.
    """
    product = db.first_or_404(sa.select(Books).where(Books.id == product_id))
    form = RatingForm()

    return render_template(
        "book.jinja2",
        title=product.book_title,
        product=product,
        template="product-template",
        form=form,
    )


# A route to get or set the user's reading position
@product_blueprint.route("/position", methods=["GET", "POST"])
def position():
    if current_user.is_authenticated:
        try:
            db.session.scalar(sa.select(CacheEntry))
        except Exception as e:
            print(e)
            db.create_all("cache_db")
        book_id = request.args.get("book_id")
        key = f"book_{book_id}_position"

        if request.method == "POST":
            # Save the current position
            book_position = request.json.get("position", 0)
            cache.set(key=key, value=book_position)

            return jsonify({"message": "Position saved!"}), 200
        else:
            # Return the current position
            position = cache.get(key)

            if position is None:
                position = 0  # default position if none is set
            return jsonify({"position": position})
    else:
        return jsonify({"message": "Guest User", "position": 0}), 200


@product_blueprint.route("/books/<id>", methods=["GET", "POST"])
def book_data(id):
    return db.first_or_404(sa.select(Books.book_blob).where(Books.id == id))


@product_blueprint.route("/rating/<book_id>/<rating>", methods=["POST"])
@login_required
def book_rate(book_id, rating):
    current_user.rate_book(book_id, rating)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "rating": db.session.scalar(
                sa.select(Books.rating).where(Books.id == book_id)
            ),
        }
    )


@product_blueprint.route("/has_rated/<book_id>", methods=["POST"])
@login_required
def user_rated(book_id):
    book = db.first_or_404(sa.select(Books).where(Books.id == book_id))
    if current_user.has_rated_book(book):
        db.session.scalar(
            sa.select(BookRated).where(
                BookRated.book_id == book_id, BookRated.user_id == current_user.id
            )
        )
        return jsonify(
            {
                "success": True,
                "rating": db.session.scalar(
                    sa.select(BookRated.rating).where(
                        BookRated.book_id == book_id,
                        BookRated.user_id == current_user.id,
                    )
                ),
            }
        )
    else:
        return jsonify({"success": True, "rating": 0})
