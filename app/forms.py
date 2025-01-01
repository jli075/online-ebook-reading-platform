from flask import request
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    FloatField,
    DateField,
)
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from wtforms.widgets import RadioInput
from flask_wtf.file import FileField, FileAllowed, FileRequired
import sqlalchemy as sa
from app import db
from app.models import Users
from datetime import date


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired()], render_kw={"autofocus": True}
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired()], render_kw={"autofocus": True}
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(
            sa.select(Users).where(Users.username == username.data)
        )
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = db.session.scalar(sa.select(Users).where(Users.email == email.data))
        if user is not None:
            raise ValidationError("Please use a different email address.")


class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    about_me = TextAreaField(
        "About me", validators=[Length(min=0, max=140)], render_kw={"autofocus": True}
    )
    submit = SubmitField("Submit")


class UploadBookForm(FlaskForm):
    epub_file = FileField(
        label="ePub File",
        id="epub_file",
        render_kw={"accept": ".epub"},
        validators=[FileRequired(), FileAllowed(["epub"], "ePub files only!")],
    )
    title = StringField(
        label="Title",
        render_kw={"placeholder": "Enter book title"},
        id="title",
        validators=[DataRequired()],
    )
    author = StringField(
        label="Author",
        render_kw={"placeholder": "Enter author's name"},
        id="author",
        validators=[DataRequired()],
    )
    cover_image = FileField(
        label="Cover Image",
        render_kw={"accept": ".jpg, .jpeg, .png"},
        id="cover_image",
        validators=[
            FileRequired(),
            FileAllowed(["jpg", "jpeg", "png"], "Images only!"),
        ],
    )
    publication_date = DateField(
        label="Publication Date",
        render_kw={"placeholder": "YYYY-MM-DD"},
        id="publication_date",
        format="%Y-%m-%d",
        default=date.today(),
        validators=[DataRequired()],
    )
    isbn = StringField(
        label="ISBN",
        render_kw={"placeholder": "Enter ISBN number (optional)"},
        id="isbn",
    )

    submit = SubmitField(label="Upload Book")


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


class StarRatingWidget(RadioInput):
    def __init__(self, number_of_stars=5):
        self.number_of_stars = number_of_stars
        self.label = None

    def __call__(self, field, **kwargs):
        html = '<div class="form-rating">'
        for i in range(self.number_of_stars, 0, -1):
            html += f"""
                <input type="radio" id="star{i}" name="rating" value="{i}" {'checked' if field.data == i else ''} class="star-input">
                <label class = "full" for="star{i}"></label>

                <input type="radio" id="star{i-1 if i-1 != 0 else ""}half" name="rating" value="{i - 0.5}" {'checked' if field.data == (i - 0.5) else ''} class="star-input">
                <label class="half" for="star{i-1 if i-1 != 0 else ""}half"></label>
            
            """
        html += "</div>"
        return html

 
class RatingForm(FlaskForm):
    rating = FloatField(
        label="", default=0, validators=[DataRequired()], widget=StarRatingWidget()
    )


class SearchForm(FlaskForm):
    q = StringField("Search")  # , validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}
        super(SearchForm, self).__init__(*args, **kwargs)
