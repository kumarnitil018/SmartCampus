"""
student_routes.py
-----------------
Student-only API endpoints.

All student routes are mounted from app.py as:

/api/students/...

Available endpoints:

GET /api/students/profile
GET /api/students/dashboard
GET /api/students/attendance
GET /api/students/subject-attendance
GET /api/students/monthly-attendance
"""

from flask import Blueprint, jsonify, session

from db import query


# ============================================================
# STUDENT BLUEPRINT
# ============================================================

# IMPORTANT:
# app.py already adds /api/students
# Therefore DO NOT add another url_prefix here.

student_bp = Blueprint(
    "student",
    __name__
)


# ============================================================
# GET CURRENT STUDENT
# ============================================================

def get_current_student():

    user_id = session.get("user_id")

    if not user_id:
        return None

    rows = query(
        """
        SELECT
            u.id AS user_id,
            u.username,
            u.email,
            u.role,

            s.id AS student_id,
            s.roll_number,
            s.full_name,
            s.course,
            s.branch,
            s.semester,
            s.phone

        FROM users u

        LEFT JOIN students s
            ON s.user_id = u.id

        WHERE u.id = %s
        """,
        (user_id,)
    )

    if not rows:
        return None

    return rows[0]


# ============================================================
# STUDENT PROFILE
# ============================================================

@student_bp.get("/profile")
def student_profile():

    student = get_current_student()

    if not student:
        return jsonify({
            "success": False,
            "error": "Student not logged in"
        }), 401

    if not student.get("student_id"):
        return jsonify({
            "success": False,
            "error": "Student profile not found"
        }), 404

    return jsonify({
        "success": True,
        "student": student
    })


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@student_bp.get("/dashboard")
def student_dashboard():

    student = get_current_student()

    if not student:
        return jsonify({
            "success": False,
            "error": "Student not logged in"
        }), 401

    student_id = student.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "error": "Student profile not found"
        }), 404


    # --------------------------------------------------------
    # OVERALL ATTENDANCE
    # --------------------------------------------------------

    attendance_rows = query(
        """
        SELECT

            COUNT(*) AS total_classes,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Present'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS classes_attended,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'Absent'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS classes_absent

        FROM attendance

        WHERE student_id = %s
        """,
        (student_id,)
    )


    attendance = (
        attendance_rows[0]
        if attendance_rows
        else {}
    )


    total_classes = int(
        attendance.get("total_classes") or 0
    )

    classes_attended = int(
        attendance.get("classes_attended") or 0
    )

    classes_absent = int(
        attendance.get("classes_absent") or 0
    )


    if total_classes > 0:

        attendance_percentage = round(
            (classes_attended / total_classes) * 100,
            2
        )

    else:

        attendance_percentage = 0


    # --------------------------------------------------------
    # SUBJECT-WISE ATTENDANCE
    # --------------------------------------------------------

    subject_rows = query(
        """
        SELECT

            s.id AS subject_id,
            s.subject_code,
            s.subject_name,
            s.course,
            s.branch,
            s.semester,

            COUNT(a.id) AS total_classes,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Present'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS classes_attended,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Absent'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS classes_absent

        FROM attendance a

        INNER JOIN subjects s
            ON s.id = a.subject_id

        WHERE a.student_id = %s

        GROUP BY
            s.id,
            s.subject_code,
            s.subject_name,
            s.course,
            s.branch,
            s.semester

        ORDER BY s.subject_name
        """,
        (student_id,)
    )


    subjects = []


    for subject in subject_rows:

        subject_total = int(
            subject.get("total_classes") or 0
        )

        subject_attended = int(
            subject.get("classes_attended") or 0
        )

        subject_absent = int(
            subject.get("classes_absent") or 0
        )


        if subject_total > 0:

            percentage = round(
                (subject_attended / subject_total) * 100,
                2
            )

        else:

            percentage = 0


        subjects.append({

            "subject_id":
                subject.get("subject_id"),

            "subject_code":
                subject.get("subject_code"),

            "subject_name":
                subject.get("subject_name"),

            "course":
                subject.get("course"),

            "branch":
                subject.get("branch"),

            "semester":
                subject.get("semester"),

            "total_classes":
                subject_total,

            "classes_attended":
                subject_attended,

            "classes_absent":
                subject_absent,

            "attendance_percentage":
                percentage,

            # Frontend compatibility
            "total":
                subject_total,

            "attended":
                subject_attended,

            "absent":
                subject_absent,

            "percentage":
                percentage
        })


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "student": {

            "user_id":
                student.get("user_id"),

            "username":
                student.get("username"),

            "email":
                student.get("email"),

            "student_id":
                student.get("student_id"),

            "roll_number":
                student.get("roll_number"),

            "full_name":
                student.get("full_name"),

            "course":
                student.get("course"),

            "branch":
                student.get("branch"),

            "semester":
                student.get("semester"),

            "phone":
                student.get("phone")
        },


        "attendance": {

            "attendance_percentage":
                attendance_percentage,

            "total_classes":
                total_classes,

            "classes_attended":
                classes_attended,

            "classes_absent":
                classes_absent
        },


        # Frontend-friendly fields
        "total_subjects":
            len(subjects),

        "total_classes":
            total_classes,

        "attended":
            classes_attended,

        "absent":
            classes_absent,

        "percentage":
            attendance_percentage,

        "subjects":
            subjects
    })


# ============================================================
# DATE-WISE ATTENDANCE
# ============================================================

@student_bp.get("/attendance")
def student_attendance():

    student = get_current_student()

    if not student:
        return jsonify({
            "success": False,
            "error": "Student not logged in"
        }), 401


    student_id = student.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "error": "Student profile not found"
        }), 404


    rows = query(
        """
        SELECT

            a.id,
            a.date,
            a.status,

            s.id AS subject_id,
            s.subject_code,
            s.subject_name

        FROM attendance a

        INNER JOIN subjects s
            ON s.id = a.subject_id

        WHERE a.student_id = %s

        ORDER BY
            a.date DESC,
            s.subject_name
        """,
        (student_id,)
    )


    return jsonify(rows)


# ============================================================
# SUBJECT-WISE ATTENDANCE
# ============================================================

@student_bp.get("/subject-attendance")
def student_subject_attendance():

    student = get_current_student()

    if not student:
        return jsonify({
            "success": False,
            "error": "Student not logged in"
        }), 401


    student_id = student.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "error": "Student profile not found"
        }), 404


    rows = query(
        """
        SELECT

            s.id AS subject_id,
            s.subject_code,
            s.subject_name,
            s.course,
            s.branch,
            s.semester,

            COUNT(a.id) AS total,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Present'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS attended,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Absent'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS absent

        FROM attendance a

        INNER JOIN subjects s
            ON s.id = a.subject_id

        WHERE a.student_id = %s

        GROUP BY

            s.id,
            s.subject_code,
            s.subject_name,
            s.course,
            s.branch,
            s.semester

        ORDER BY s.subject_name
        """,
        (student_id,)
    )


    result = []


    for row in rows:

        total = int(row.get("total") or 0)

        attended = int(
            row.get("attended") or 0
        )

        absent = int(
            row.get("absent") or 0
        )


        percentage = (
            round((attended / total) * 100, 2)
            if total > 0
            else 0
        )


        result.append({

            "subject_id":
                row.get("subject_id"),

            "subject_code":
                row.get("subject_code"),

            "subject_name":
                row.get("subject_name"),

            "course":
                row.get("course"),

            "branch":
                row.get("branch"),

            "semester":
                row.get("semester"),

            "total":
                total,

            "attended":
                attended,

            "absent":
                absent,

            "percentage":
                percentage
        })


    return jsonify(result)


# ============================================================
# MONTHLY ATTENDANCE
# ============================================================

@student_bp.get("/monthly-attendance")
def student_monthly_attendance():

    student = get_current_student()

    if not student:
        return jsonify({
            "success": False,
            "error": "Student not logged in"
        }), 401


    student_id = student.get("student_id")


    if not student_id:
        return jsonify({
            "success": False,
            "error": "Student profile not found"
        }), 404


    rows = query(
        """
        SELECT

            TO_CHAR(
                a.date,
                'YYYY-MM'
            ) AS month,

            COUNT(*) AS total,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Present'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS attended,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Absent'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS absent

        FROM attendance a

        WHERE a.student_id = %s

        GROUP BY
            TO_CHAR(a.date, 'YYYY-MM')

        ORDER BY month DESC
        """,
        (student_id,)
    )


    result = []


    for row in rows:

        total = int(
            row.get("total") or 0
        )

        attended = int(
            row.get("attended") or 0
        )

        absent = int(
            row.get("absent") or 0
        )


        percentage = (
            round((attended / total) * 100, 2)
            if total > 0
            else 0
        )


        result.append({

            "month":
                row.get("month"),

            "total":
                total,

            "attended":
                attended,

            "absent":
                absent,

            "percentage":
                percentage
        })


    return jsonify(result)