"""student.py – database logic for the `students` table (student profiles)."""

from db import query, execute


def create_student_profile(user_id, roll_number, full_name, course, branch, semester, phone):
    return execute(
        "INSERT INTO students (user_id, roll_number, full_name, course, branch, semester, phone) "
        "VALUES (?,?,?,?,?,?,?)",
        (user_id, roll_number, full_name, course, branch, semester, phone),
    )


def get_student_by_user_id(user_id):
    return query("SELECT * FROM students WHERE user_id = ?", (user_id,), one=True)


def get_student_by_id(student_id):
    return query("SELECT * FROM students WHERE id = ?", (student_id,), one=True)


def get_student_by_roll(roll_number):
    return query("SELECT * FROM students WHERE roll_number = ?", (roll_number,), one=True)


def list_students_for_subject(course, branch, semester):
    """All students that belong to the class a subject is taught to."""
    return query(
        "SELECT * FROM students WHERE course = ? AND branch = ? AND semester = ? "
        "ORDER BY roll_number",
        (course, branch, semester),
    )
