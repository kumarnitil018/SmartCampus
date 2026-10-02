"""
teacher_routes.py
-----------------
Teacher-only endpoints.

All teacher APIs are mounted by app.py at:

    /api/teachers

Available endpoints:

    GET    /api/teachers/profile
    GET    /api/teachers/subjects
    GET    /api/teachers/available-subjects
    POST   /api/teachers/subjects
    POST   /api/teachers/subjects/assign
    DELETE /api/teachers/subjects/<id>
    GET    /api/teachers/subjects/<id>/students
    GET    /api/teachers/subjects/<id>/history
    GET    /api/teachers/subjects/<id>/report
"""

from flask import Blueprint, jsonify

from auth import role_required, current_user_id, get_json
from models import teacher as teacher_model
from models import subject as subject_model
from models import student as student_model
from models import attendance as attendance_model


# IMPORTANT:
# app.py already adds /api/teachers
# Therefore NO url_prefix is added here.
teacher_bp = Blueprint(
    "teacher",
    __name__
)


# ============================================================
# HELPER
# ============================================================

def _get_profile():
    """
    Get the currently logged-in teacher profile.
    """
    return teacher_model.get_teacher_by_user_id(
        current_user_id()
    )


# ============================================================
# TEACHER PROFILE
# ============================================================

@teacher_bp.route("/profile", methods=["GET"])
@role_required("teacher")
def profile():

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    return jsonify(teacher)


# ============================================================
# MY SUBJECTS
# ============================================================

@teacher_bp.route("/subjects", methods=["GET"])
@role_required("teacher")
def my_subjects():

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    return jsonify(
        subject_model.get_teacher_subjects(
            teacher["id"]
        )
    )


# ============================================================
# AVAILABLE SUBJECTS
# ============================================================

@teacher_bp.route(
    "/available-subjects",
    methods=["GET"]
)
@role_required("teacher")
def available_subjects():

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    mine = {
        s["id"]
        for s in subject_model.get_teacher_subjects(
            teacher["id"]
        )
    }

    available = [
        s
        for s in subject_model.list_all_subjects()
        if s["id"] not in mine
    ]

    return jsonify(available)


# ============================================================
# CREATE + ASSIGN SUBJECT
# ============================================================

@teacher_bp.route(
    "/subjects",
    methods=["POST"]
)
@role_required("teacher")
def create_and_assign_subject():

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    data = get_json()

    code = (
        data.get("subject_code") or ""
    ).strip().upper()

    name = (
        data.get("subject_name") or ""
    ).strip()

    course = (
        data.get("course") or ""
    ).strip()

    branch = (
        data.get("branch") or ""
    ).strip()

    try:
        semester = int(
            data.get("semester") or 1
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "Semester must be a valid number."
        }), 400

    if not code or not name or not course or not branch:
        return jsonify({
            "error": (
                "Subject code, name, course "
                "and branch are required."
            )
        }), 400

    existing = subject_model.get_subject_by_code(
        code
    )

    if existing:
        subject_id = existing["id"]

    else:
        subject_id = subject_model.create_subject(
            code,
            name,
            course,
            branch,
            semester
        )

    subject_model.assign_subject_to_teacher(
        teacher["id"],
        subject_id
    )

    return jsonify({
        "message": "Subject added.",
        "subject_id": subject_id
    }), 201


# ============================================================
# ASSIGN EXISTING SUBJECT
# ============================================================

@teacher_bp.route(
    "/subjects/assign",
    methods=["POST"]
)
@role_required("teacher")
def assign_subject():

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    data = get_json()

    subject_id = data.get("subject_id")

    if not subject_id:
        return jsonify({
            "error": "subject_id is required."
        }), 400

    if not subject_model.get_subject_by_id(
        subject_id
    ):
        return jsonify({
            "error": "Subject not found."
        }), 404

    subject_model.assign_subject_to_teacher(
        teacher["id"],
        subject_id
    )

    return jsonify({
        "message": "Subject assigned to you."
    })


# ============================================================
# REMOVE SUBJECT
# ============================================================

@teacher_bp.route(
    "/subjects/<int:subject_id>",
    methods=["DELETE"]
)
@role_required("teacher")
def remove_subject(subject_id):

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    if not subject_model.teacher_owns_subject(
        teacher["id"],
        subject_id
    ):
        return jsonify({
            "error": (
                "You can only remove "
                "your own subjects."
            )
        }), 403

    subject_model.unassign_subject(
        teacher["id"],
        subject_id
    )

    return jsonify({
        "message": (
            "Subject removed from your list."
        )
    })


# ============================================================
# STUDENTS OF SUBJECT
# ============================================================

@teacher_bp.route(
    "/subjects/<int:subject_id>/students",
    methods=["GET"]
)
@role_required("teacher")
def subject_students(subject_id):

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    if not subject_model.teacher_owns_subject(
        teacher["id"],
        subject_id
    ):
        return jsonify({
            "error": (
                "You are not assigned "
                "to this subject."
            )
        }), 403

    subject = subject_model.get_subject_by_id(
        subject_id
    )

    if not subject:
        return jsonify({
            "error": "Subject not found."
        }), 404

    students = student_model.list_students_for_subject(
        subject["course"],
        subject["branch"],
        subject["semester"]
    )

    return jsonify({
        "subject": subject,
        "students": students
    })


# ============================================================
# ATTENDANCE HISTORY
# ============================================================

@teacher_bp.route(
    "/subjects/<int:subject_id>/history",
    methods=["GET"]
)
@role_required("teacher")
def subject_history(subject_id):

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    if not subject_model.teacher_owns_subject(
        teacher["id"],
        subject_id
    ):
        return jsonify({
            "error": (
                "You are not assigned "
                "to this subject."
            )
        }), 403

    return jsonify({
        "records":
            attendance_model.get_history_for_subject(
                subject_id
            ),

        "dates":
            attendance_model.get_distinct_dates_for_subject(
                subject_id
            )
    })


# ============================================================
# SUBJECT REPORT
# ============================================================

@teacher_bp.route(
    "/subjects/<int:subject_id>/report",
    methods=["GET"]
)
@role_required("teacher")
def subject_report(subject_id):

    teacher = _get_profile()

    if not teacher:
        return jsonify({
            "error": "Teacher profile not found."
        }), 404

    if not subject_model.teacher_owns_subject(
        teacher["id"],
        subject_id
    ):
        return jsonify({
            "error": (
                "You are not assigned "
                "to this subject."
            )
        }), 403

    subject = subject_model.get_subject_by_id(
        subject_id
    )

    if not subject:
        return jsonify({
            "error": "Subject not found."
        }), 404

    return jsonify({
        "subject": subject,

        "report":
            attendance_model.get_subject_report(
                subject_id
            )
    })