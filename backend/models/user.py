"""user.py – database logic for the `users` table (authentication records)."""

from db import query, execute
from auth import hash_password


def create_user(username, email, password, role):
    """Insert a new user and return its id. Password is hashed first."""
    return execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?,?,?,?)",
        (username, email, hash_password(password), role),
    )


def get_user_by_username(username):
    return query("SELECT * FROM users WHERE username = ?", (username,), one=True)


def get_user_by_email(email):
    return query("SELECT * FROM users WHERE email = ?", (email,), one=True)


def get_user_by_id(user_id):
    return query("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
