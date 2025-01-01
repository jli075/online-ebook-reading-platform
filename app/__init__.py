"""Initialize Flask app."""

from flask import Flask
from flask_assets import Environment
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

from .db import db
from .cache import SQLAlchemyCache


migrate = Migrate()
bootstrap = Bootstrap5()
login = LoginManager()
cache = SQLAlchemyCache()


def create_app(config_class=Config):
    #     """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    login.init_app(app)
    cache.init_app(app)
    assets = Environment()
    assets.init_app(app)

    with app.app_context():
        # Import parts of our application
        from .assets import compile_static_assets
        from .home import home
        from .product import product
        from .profile import profile

        # Register Blueprints
        app.register_blueprint(profile.profile_blueprint)
        app.register_blueprint(home.home_blueprint)
        app.register_blueprint(product.product_blueprint)

        # Compile static assets
        compile_static_assets(assets)

        return app
