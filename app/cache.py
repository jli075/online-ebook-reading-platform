# /app/cache.py
from pickle import dumps, loads
from time import time
from .db import db
from flask_login import current_user
from sys import maxsize
import sqlalchemy as sa


class SQLAlchemyCache:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.db = db

    def set(self, key, value, timeout=None):
        if timeout is None:
            expiration = maxsize  # Set expiration to a very far future (no expiration)
        else:
            expiration = int(time()) + timeout  # Expiration time (in seconds)

        # Import CacheEntry locally to avoid circular imports
        from .models import CacheEntry

        cache_entry = db.session.scalar(
            sa.select(CacheEntry).where(
                CacheEntry.user_id == current_user.id, CacheEntry.key == key
            )
        )
        if cache_entry:
            cache_entry.value = dumps(value)
            cache_entry.expiration = expiration
        else:
            cache_entry = CacheEntry(
                key=key,
                value=dumps(value),
                expiration=expiration,
                user_id=current_user.id,
            )
            self.db.session.add(cache_entry)
        self.db.session.commit()

    def get(self, key):
        # Import CacheEntry locally to avoid circular imports
        from .models import CacheEntry

        cache_entry = db.session.scalar(
            sa.select(CacheEntry).where(
                CacheEntry.user_id == current_user.id, CacheEntry.key == key
            )
        )

        if cache_entry:
            # If expiration is maxsize, we consider it as "never expiring"
            if cache_entry.expiration == maxsize or cache_entry.expiration > int(
                time()
            ):
                return loads(cache_entry.value)  # Unpickle and return the value
        return None

    def delete(self, key):
        # Import CacheEntry locally to avoid circular imports
        from .models import CacheEntry

        cache_entry = db.session.scalar(
            sa.select(CacheEntry).where(
                CacheEntry.user_id == current_user.id, CacheEntry.key == key
            )
        )
        if cache_entry:
            self.db.session.delete(cache_entry)
            self.db.session.commit()

    def clear(self):
        # Import CacheEntry locally to avoid circular imports
        from .models import CacheEntry

        self.db.session.query(CacheEntry).delete()
        self.db.session.commit()
