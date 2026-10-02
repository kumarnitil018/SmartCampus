"""
config.py
---------
Central configuration for SmartCampus.

This version is prepared for:
- Local development
- Supabase PostgreSQL
- Production deployment
- Secure environment variables
"""

import os

from dotenv import load_dotenv


# ------------------------------------------------------------
# BASE DIRECTORY
# ------------------------------------------------------------

# SmartCampus/
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# ------------------------------------------------------------
# LOAD .env FILE
# ------------------------------------------------------------

# .env is located in the SmartCampus root folder.
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

# PostgreSQL / Supabase connection string.
#
# Example:
# DATABASE_URL=postgresql://postgres:password@host:5432/postgres
#
# IMPORTANT:
# Do not write the real password directly inside Python code.

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


# ------------------------------------------------------------
# DATABASE SCHEMA
# ------------------------------------------------------------

SCHEMA_PATH = os.path.join(
    BASE_DIR,
    "database",
    "database.sql"
)


# ------------------------------------------------------------
# FRONTEND
# ------------------------------------------------------------

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)


# ------------------------------------------------------------
# SECRET KEY
# ------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "SMARTCAMPUS_SECRET",
    "smartcampus-dev-secret-change-me"
)


# ------------------------------------------------------------
# SESSION
# ------------------------------------------------------------

# 8 hours
SESSION_LIFETIME = 60 * 60 * 8


# ------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------

SMARTCAMPUS_ENV = os.environ.get(
    "SMARTCAMPUS_ENV",
    "development"
).lower()


# ------------------------------------------------------------
# DEBUG
# ------------------------------------------------------------

DEBUG = os.environ.get(
    "DEBUG",
    "1"
) == "1"


# ------------------------------------------------------------
# PRODUCTION CHECK
# ------------------------------------------------------------

if SMARTCAMPUS_ENV == "production":

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    if SECRET_KEY == "smartcampus-dev-secret-change-me":
        raise RuntimeError(
            "SMARTCAMPUS_SECRET must be changed in production."
        )