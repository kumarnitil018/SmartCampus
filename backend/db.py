"""
db.py
-----
SmartCampus database helpers.

Database:
    PostgreSQL / Supabase

This file handles:
    - PostgreSQL connection
    - SELECT queries
    - INSERT / UPDATE / DELETE
    - Flask request database connection
    - Database initialization
    - Demo data
"""

import psycopg
from psycopg.rows import dict_row
from flask import g
from werkzeug.security import generate_password_hash

from config import DATABASE_URL, SCHEMA_PATH


# ============================================================
# REQUEST DATABASE CONNECTION
# ============================================================

def get_db():
    """
    Get a PostgreSQL connection for the current Flask request.
    """

    if "db" not in g:

        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not configured."
            )

        g.db = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row,
            sslmode="require",
        )

    return g.db


# ============================================================
# CLOSE REQUEST CONNECTION
# ============================================================

def close_db(exception=None):
    """
    Close the request database connection.
    """

    db = g.pop("db", None)

    if db is not None:
        db.close()


# ============================================================
# SQL PREPARATION
# ============================================================

def _prepare_sql(sql):
    """
    Convert old SQLite-style placeholders to PostgreSQL.

    SQLite:
        ?

    PostgreSQL:
        %s
    """

    sql = sql.replace("?", "%s")

    return sql


# ============================================================
# SELECT
# ============================================================

def query(sql, params=(), one=False):
    """
    Execute SELECT query.
    """

    db = get_db()

    prepared_sql = _prepare_sql(sql)

    with db.cursor() as cursor:

        cursor.execute(
            prepared_sql,
            params
        )

        rows = cursor.fetchall()

    if one:
        return rows[0] if rows else None

    return rows


# ============================================================
# INSERT / UPDATE / DELETE
# ============================================================

def execute(sql, params=()):
    """
    Execute INSERT / UPDATE / DELETE.

    For INSERT statements, return the generated ID.
    """

    db = get_db()

    prepared_sql = _prepare_sql(sql)

    is_insert = (
        prepared_sql
        .lstrip()
        .upper()
        .startswith("INSERT")
    )

    try:

        with db.cursor() as cursor:

            if is_insert:

                # ------------------------------------------------
                # Add RETURNING id if the query doesn't already
                # contain RETURNING.
                # ------------------------------------------------

                if "RETURNING" not in prepared_sql.upper():

                    prepared_sql = prepared_sql.rstrip()

                    if prepared_sql.endswith(";"):
                        prepared_sql = prepared_sql[:-1]

                    prepared_sql += " RETURNING id"

                cursor.execute(
                    prepared_sql,
                    params
                )

                row = cursor.fetchone()

                db.commit()

                if row:
                    return row["id"]

                return None

            # ----------------------------------------------------
            # UPDATE / DELETE
            # ----------------------------------------------------

            cursor.execute(
                prepared_sql,
                params
            )

        db.commit()

        return None

    except Exception:

        db.rollback()

        raise


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Create PostgreSQL tables and seed demo data.

    IMPORTANT:
    This function does NOT use Flask's g object.
    Therefore it can safely be called while the application
    is starting.
    """

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL is missing."
        )

    # --------------------------------------------------------
    # Read schema
    # --------------------------------------------------------

    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        schema = file.read()

    # --------------------------------------------------------
    # Create one direct PostgreSQL connection.
    #
    # This connection is independent of Flask's `g`.
    # --------------------------------------------------------

    with psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        sslmode="require",
    ) as connection:

        try:

            with connection.cursor() as cursor:

                # ------------------------------------------------
                # Execute schema statements.
                # ------------------------------------------------

                statements = [
                    statement.strip()
                    for statement in schema.split(";")
                    if statement.strip()
                ]

                for statement in statements:

                    cursor.execute(statement)

            connection.commit()

        except Exception:

            connection.rollback()

            raise

        # --------------------------------------------------------
        # Seed demo data using THE SAME DIRECT CONNECTION.
        # --------------------------------------------------------

        seed_demo_data(connection)


# ============================================================
# DEMO DATA
# ============================================================

def seed_demo_data(connection):
    """
    Insert demo teacher, student, subjects and attendance.

    This function deliberately receives a direct PostgreSQL
    connection instead of using Flask's `g`.
    """

    try:

        with connection.cursor() as cursor:

            # ==================================================
            # DEMO TEACHER USER
            # ==================================================

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = %s
                """,
                ("prof.sharma",)
            )

            teacher_user = cursor.fetchone()

            if teacher_user is None:

                cursor.execute(
                    """
                    INSERT INTO users
                    (
                        username,
                        email,
                        password_hash,
                        role
                    )
                    VALUES
                    (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        "prof.sharma",
                        "sharma@smartcampus.edu",
                        generate_password_hash(
                            "teacher123"
                        ),
                        "teacher",
                    ),
                )

                teacher_user_id = (
                    cursor.fetchone()["id"]
                )

                cursor.execute(
                    """
                    INSERT INTO teachers
                    (
                        user_id,
                        full_name,
                        department,
                        employee_id,
                        phone
                    )
                    VALUES
                    (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        teacher_user_id,
                        "Prof. Rajesh Sharma",
                        "Computer Science",
                        "T-1001",
                        "9876500001",
                    ),
                )

                teacher_id = (
                    cursor.fetchone()["id"]
                )

            else:

                # Existing demo teacher.
                cursor.execute(
                    """
                    SELECT id
                    FROM teachers
                    WHERE user_id = %s
                    """,
                    (
                        teacher_user["id"],
                    )
                )

                teacher_row = cursor.fetchone()

                if teacher_row:

                    teacher_id = teacher_row["id"]

                else:

                    cursor.execute(
                        """
                        INSERT INTO teachers
                        (
                            user_id,
                            full_name,
                            department,
                            employee_id,
                            phone
                        )
                        VALUES
                        (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            teacher_user["id"],
                            "Prof. Rajesh Sharma",
                            "Computer Science",
                            "T-1001",
                            "9876500001",
                        ),
                    )

                    teacher_id = (
                        cursor.fetchone()["id"]
                    )

            # ==================================================
            # DEMO SUBJECT 1
            # ==================================================

            cursor.execute(
                """
                INSERT INTO subjects
                (
                    subject_code,
                    subject_name,
                    course,
                    branch,
                    semester
                )
                VALUES
                (%s, %s, %s, %s, %s)
                ON CONFLICT (subject_code)
                DO NOTHING
                """,
                (
                    "CS301",
                    "Data Structures",
                    "B.Tech",
                    "CSE",
                    3,
                ),
            )

            cursor.execute(
                """
                SELECT id
                FROM subjects
                WHERE subject_code = %s
                """,
                ("CS301",)
            )

            subject1 = cursor.fetchone()

            # ==================================================
            # DEMO SUBJECT 2
            # ==================================================

            cursor.execute(
                """
                INSERT INTO subjects
                (
                    subject_code,
                    subject_name,
                    course,
                    branch,
                    semester
                )
                VALUES
                (%s, %s, %s, %s, %s)
                ON CONFLICT (subject_code)
                DO NOTHING
                """,
                (
                    "CS302",
                    "Database Systems",
                    "B.Tech",
                    "CSE",
                    3,
                ),
            )

            cursor.execute(
                """
                SELECT id
                FROM subjects
                WHERE subject_code = %s
                """,
                ("CS302",)
            )

            subject2 = cursor.fetchone()

            # ==================================================
            # TEACHER SUBJECTS
            # ==================================================

            if teacher_id and subject1:

                cursor.execute(
                    """
                    INSERT INTO teacher_subjects
                    (
                        teacher_id,
                        subject_id
                    )
                    VALUES
                    (%s, %s)
                    ON CONFLICT
                    (
                        teacher_id,
                        subject_id
                    )
                    DO NOTHING
                    """,
                    (
                        teacher_id,
                        subject1["id"],
                    ),
                )

            if teacher_id and subject2:

                cursor.execute(
                    """
                    INSERT INTO teacher_subjects
                    (
                        teacher_id,
                        subject_id
                    )
                    VALUES
                    (%s, %s)
                    ON CONFLICT
                    (
                        teacher_id,
                        subject_id
                    )
                    DO NOTHING
                    """,
                    (
                        teacher_id,
                        subject2["id"],
                    ),
                )

            # ==================================================
            # DEMO STUDENT
            # ==================================================

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = %s
                """,
                ("aarav",)
            )

            student_user = cursor.fetchone()

            if student_user is None:

                cursor.execute(
                    """
                    INSERT INTO users
                    (
                        username,
                        email,
                        password_hash,
                        role
                    )
                    VALUES
                    (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        "aarav",
                        "aarav@smartcampus.edu",
                        generate_password_hash(
                            "student123"
                        ),
                        "student",
                    ),
                )

                student_user_id = (
                    cursor.fetchone()["id"]
                )

                cursor.execute(
                    """
                    INSERT INTO students
                    (
                        user_id,
                        roll_number,
                        full_name,
                        course,
                        branch,
                        semester,
                        phone
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (roll_number)
                    DO NOTHING
                    """,
                    (
                        student_user_id,
                        "CSE-2023-001",
                        "Aarav Mehta",
                        "B.Tech",
                        "CSE",
                        3,
                        "9876500002",
                    ),
                )

            # ==================================================
            # GET STUDENT
            # ==================================================

            cursor.execute(
                """
                SELECT id
                FROM students
                WHERE roll_number = %s
                """,
                ("CSE-2023-001",)
            )

            student = cursor.fetchone()

            # ==================================================
            # DEMO ATTENDANCE
            # ==================================================

            if (
                student
                and teacher_id
                and subject1
                and subject2
            ):

                attendance_rows = [

                    (
                        student["id"],
                        subject1["id"],
                        teacher_id,
                        "2025-01-06",
                        "Present",
                    ),

                    (
                        student["id"],
                        subject1["id"],
                        teacher_id,
                        "2025-01-08",
                        "Present",
                    ),

                    (
                        student["id"],
                        subject1["id"],
                        teacher_id,
                        "2025-01-10",
                        "Absent",
                    ),

                    (
                        student["id"],
                        subject1["id"],
                        teacher_id,
                        "2025-01-13",
                        "Present",
                    ),

                    (
                        student["id"],
                        subject1["id"],
                        teacher_id,
                        "2025-01-15",
                        "Present",
                    ),

                    (
                        student["id"],
                        subject2["id"],
                        teacher_id,
                        "2025-01-07",
                        "Present",
                    ),

                    (
                        student["id"],
                        subject2["id"],
                        teacher_id,
                        "2025-01-09",
                        "Present",
                    ),

                    (
                        student["id"],
                        subject2["id"],
                        teacher_id,
                        "2025-01-12",
                        "Present",
                    ),

                    (
                        student["id"],
                        subject2["id"],
                        teacher_id,
                        "2025-01-14",
                        "Absent",
                    ),

                    (
                        student["id"],
                        subject2["id"],
                        teacher_id,
                        "2025-01-16",
                        "Present",
                    ),
                ]

                for row in attendance_rows:

                    cursor.execute(
                        """
                        INSERT INTO attendance
                        (
                            student_id,
                            subject_id,
                            teacher_id,
                            date,
                            status
                        )
                        VALUES
                        (%s, %s, %s, %s, %s)
                        ON CONFLICT
                        (
                            student_id,
                            subject_id,
                            date
                        )
                        DO NOTHING
                        """,
                        row,
                    )

        connection.commit()

    except Exception:

        connection.rollback()

        raise