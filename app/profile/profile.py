"""Routes for logged-in profile."""

from urllib.parse import urlsplit
from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    request,
)
from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required,
)
import sqlalchemy as sa
from app.forms import (
    LoginForm,
    RegistrationForm,
    EditProfileForm,
    EmptyForm,
    UploadBookForm,
)
from app import db, login

from app.models import Users, Books, followers, BookLike


# Blueprint Configuration
profile_blueprint = Blueprint(
    "profile_blueprint", __name__, template_folder="templates", static_folder="static"
)


@login.unauthorized_handler
def handle_needs_login():
    flash("You have to be logged in to access this page.")
    return redirect(url_for("profile_blueprint.login", next=request.full_path))


@profile_blueprint.route("/profile/<username>", methods=["GET"])
@login_required
def user_profile(username):
    """
    Logged-in user profile page.
    """
    user = db.first_or_404(sa.select(Users).where(Users.username == username))
    form = EmptyForm()

    query = (
        sa.select(Books)
        .where(Books.user_id == user.id)
        .order_by(Books.publish_date.desc())
    )
    posts = db.session.scalars(query).all()

    query = (
        sa.select(Users)
        .join(followers, Users.id == followers.columns.get("followed_id"), isouter=True)
        .where(user.id == followers.columns.get("follower_id"))
    )
    authors = db.session.scalars(query).all()

    query = (
        sa.select(Books)
        .join(BookLike, Books.id == BookLike.book_id)
        .where(user.id == BookLike.user_id)
    )
    liked = db.session.scalars(query).all()

    return render_template(
        "my_account.jinja2",
        title="User Profile",
        template="profile-template",
        user=user,
        form=form,
        posts=posts,
        liked=liked,
        authors=authors,
    )


@profile_blueprint.route("/profile/redirect/<user_id>", methods=["GET", "POST"])
@login_required
def user_redirect(user_id):
    user = db.first_or_404(sa.select(Users).where(Users.id == user_id))
    return redirect(url_for("profile_blueprint.user_profile", username=user.username))


@profile_blueprint.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(
            url_for("profile_blueprint.user_profile", username=current_user.username)
        )
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template(
        "edit_profile.jinja2",
        title="Edit Profile",
        template="profile-template",
        form=form,
    )


@profile_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(
            url_for("profile_blueprint.user_profile", username=current_user.username)
        )
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(Users).where(Users.username == form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            print("failed login")
            return redirect(
                url_for("profile_blueprint.login", next=request.args.get("next"))
            )
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for(
                "profile_blueprint.user_profile", username=current_user.username
            )
        return redirect(next_page)
    return render_template(
        "login.jinja2", title="Sign In", template="profile-template", form=form
    )


@profile_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home_blueprint.home"))


@profile_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home_blueprint.home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("profile_blueprint.login"))
    return render_template(
        "register.jinja2", title="Register", template="profile-template", form=form
    )


@profile_blueprint.route("/upload_book", methods=["GET", "POST"])
@login_required
def upload_book():
    form = UploadBookForm()
    if form.validate_on_submit():
        new_book = Books(
            book_title=form.title.data,
            author=form.author.data,
            publish_date=form.publication_date.data,
            isbn=form.isbn.data if form.isbn.data else 0,
            cover_image=form.cover_image.data.stream._file.read(),
            book_blob=form.epub_file.data.stream._file.read(),
            user_id=current_user.id,
        )
        db.session.add(new_book)
        db.session.commit()

        return redirect(
            url_for("profile_blueprint.user_profile", username=current_user.username)
        )

    return render_template(
        "upload_book.jinja2",
        title="Upload Book",
        template="profile-template",
        form=form,
    )
