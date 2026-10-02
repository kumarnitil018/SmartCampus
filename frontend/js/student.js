/* ============================================================
   student.js
   SmartCampus - Student Panel

   Handles:
   - Student Dashboard
   - Date-wise Attendance
   - Subject-wise Attendance
   - Monthly Attendance

   Backend prefix:
   /api/students
   ============================================================ */


document.addEventListener("DOMContentLoaded", async () => {

    const user = await requireRole("student");

    if (!user) {
        return;
    }

    markActiveNav();

    const nameEl = document.getElementById("userName");

    if (nameEl) {
        nameEl.textContent = user.username || "Student";
    }

    const page = document.body.dataset.page;

    try {

        if (page === "dashboard") {
            await loadDashboard();
        }

        if (page === "attendance") {
            await loadAttendance();
        }

        if (page === "subject") {
            await loadSubjectAttendance();
        }

        if (page === "monthly") {
            await loadMonthly();
        }

    } catch (error) {

        console.error("Student page error:", error);

        showPageError(
            "Unable to load data. Please refresh the page and try again."
        );
    }
});


/* ============================================================
   STUDENT DASHBOARD
   ============================================================ */

async function loadDashboard() {

    const d = await api("/api/students/dashboard");

    if (!d || d.success === false) {

        throw new Error(
            d?.error || "Unable to load student dashboard"
        );
    }


    /* --------------------------------------------------------
       Student information
       -------------------------------------------------------- */

    const student = d.student || {};

    const studentName =
        student.full_name ||
        student.username ||
        "Student";

    const rollNumber =
        student.roll_number ||
        "-";

    const course =
        student.course ||
        "-";

    const branch =
        student.branch ||
        "-";

    const semester =
        student.semester ??
        "-";


    const studentNameEl =
        document.getElementById("studentName");

    if (studentNameEl) {
        studentNameEl.textContent = studentName;
    }


    const rollEl =
        document.getElementById("rollNumber");

    if (rollEl) {
        rollEl.textContent = rollNumber;
    }


    const courseEl =
        document.getElementById("courseInfo");

    if (courseEl) {

        courseEl.textContent =
            `${course} • ${branch} • Semester ${semester}`;
    }


    /* --------------------------------------------------------
       Attendance data
       -------------------------------------------------------- */

    const attendance =
        d.attendance || {};


    const totalClasses =
        Number(attendance.total_classes || 0);

    const attended =
        Number(attendance.classes_attended || 0);

    const absent =
        Number(attendance.classes_absent || 0);

    let percentage =
        Number(
            attendance.attendance_percentage || 0
        );


    if (
        !Number.isFinite(percentage) ||
        percentage < 0
    ) {

        percentage =
            totalClasses > 0
                ? (attended / totalClasses) * 100
                : 0;
    }


    percentage =
        Math.max(
            0,
            Math.min(
                100,
                Number(percentage.toFixed(2))
            )
        );


    /* --------------------------------------------------------
       Subjects
       -------------------------------------------------------- */

    const subjects =
        Array.isArray(d.subjects)
            ? d.subjects
            : [];


    /* --------------------------------------------------------
       Dashboard statistics
       -------------------------------------------------------- */

    const statSubjects =
        document.getElementById("statSubjects");

    if (statSubjects) {
        statSubjects.textContent = subjects.length;
    }


    const statTotal =
        document.getElementById("statTotal");

    if (statTotal) {
        statTotal.textContent = totalClasses;
    }


    const statAttended =
        document.getElementById("statAttended");

    if (statAttended) {
        statAttended.textContent = attended;
    }


    const statAbsent =
        document.getElementById("statAbsent");

    if (statAbsent) {
        statAbsent.textContent = absent;
    }


    /* --------------------------------------------------------
       Percentage Ring
       -------------------------------------------------------- */

    const ring =
        document.getElementById("ring");

    if (ring) {

        ring.style.setProperty(
            "--val",
            percentage
        );
    }


    const ringVal =
        document.getElementById("ringVal");

    if (ringVal) {
        ringVal.textContent = percentage + "%";
    }


    /* --------------------------------------------------------
       Overall attendance message
       -------------------------------------------------------- */

    const overallText =
        document.getElementById("overallText");

    if (overallText) {

        if (totalClasses === 0) {

            overallText.textContent =
                "No attendance has been recorded yet.";

        } else if (percentage >= 75) {

            overallText.textContent =
                "Great! You are above the 75% requirement.";

        } else if (percentage >= 50) {

            overallText.textContent =
                "Warning: try to attend more classes.";

        } else {

            overallText.textContent =
                "Low attendance – please improve.";
        }
    }


    /* --------------------------------------------------------
       Subject-wise progress
       -------------------------------------------------------- */

    const list =
        document.getElementById("subjectList");

    if (!list) {
        return;
    }


    if (!subjects.length) {

        list.innerHTML = `
            <p class="muted">
                No attendance recorded yet.
            </p>
        `;

        return;
    }


    list.innerHTML =
        subjects.map(subject => {

            const subjectTotal =
                Number(
                    subject.total_classes ??
                    subject.total ??
                    0
                );

            const subjectAttended =
                Number(
                    subject.classes_attended ??
                    subject.attended ??
                    0
                );

            let subjectPercentage =
                Number(
                    subject.attendance_percentage ??
                    subject.percentage ??
                    0
                );


            if (
                subjectTotal > 0 &&
                (
                    subject.attendance_percentage === undefined &&
                    subject.percentage === undefined
                )
            ) {

                subjectPercentage =
                    (subjectAttended / subjectTotal) * 100;
            }


            subjectPercentage =
                Math.max(
                    0,
                    Math.min(
                        100,
                        Number(
                            subjectPercentage.toFixed(2)
                        )
                    )
                );


            return `
                <div class="subj-row">

                    <div>

                        <div class="name">
                            ${esc(
                                subject.subject_name ||
                                "Unknown Subject"
                            )}
                        </div>

                        <div
                            class="muted"
                            style="font-size:.8rem"
                        >
                            ${esc(
                                subject.subject_code ||
                                "-"
                            )}
                        </div>

                    </div>


                    <div class="progress">

                        <i
                            class="${pctClass(subjectPercentage)}"
                            style="width:${subjectPercentage}%"
                        ></i>

                    </div>


                    <div class="pct">
                        ${subjectPercentage}%
                    </div>

                </div>
            `;

        }).join("");
}


/* ============================================================
   DATE-WISE ATTENDANCE
   ============================================================ */

async function loadAttendance() {

    const records =
        await api("/api/students/attendance");


    const tbody =
        document.getElementById("recordsBody");

    const filter =
        document.getElementById("subjectFilter");


    if (!tbody) {
        return;
    }


    const attendanceRecords =
        Array.isArray(records)
            ? records
            : [];


    /* --------------------------------------------------------
       Subject filter
       -------------------------------------------------------- */

    if (filter) {

        const subjects =
            [
                ...new Set(
                    attendanceRecords
                        .map(record => record.subject_name)
                        .filter(Boolean)
                )
            ];


        filter.innerHTML = `
            <option value="">All Subjects</option>
        `;


        subjects.forEach(subject => {

            filter.insertAdjacentHTML(
                "beforeend",
                `
                    <option value="${esc(subject)}">
                        ${esc(subject)}
                    </option>
                `
            );
        });
    }


    /* --------------------------------------------------------
       Render attendance table
       -------------------------------------------------------- */

    const render = (rows) => {

        if (!rows.length) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="4"
                        class="muted"
                    >
                        No records found.
                    </td>
                </tr>
            `;

            return;
        }


        tbody.innerHTML =
            rows.map(record => {

                const status =
                    record.status || "-";


                const statusClass =
                    status.toLowerCase() === "present"
                        ? "present"
                        : "absent";


                return `
                    <tr>

                        <td>
                            ${prettyDate(record.date)}
                        </td>

                        <td>
                            ${esc(
                                record.subject_name || "-"
                            )}
                        </td>

                        <td>
                            ${esc(
                                record.subject_code || "-"
                            )}
                        </td>

                        <td>

                            <span
                                class="badge badge-${statusClass}"
                            >
                                ${esc(status)}
                            </span>

                        </td>

                    </tr>
                `;

            }).join("");
    };


    render(attendanceRecords);


    /* --------------------------------------------------------
       Filter event
       -------------------------------------------------------- */

    if (filter) {

        filter.addEventListener(
            "change",
            () => {

                const value =
                    filter.value;


                if (!value) {

                    render(
                        attendanceRecords
                    );

                    return;
                }


                render(
                    attendanceRecords.filter(
                        record =>
                            record.subject_name === value
                    )
                );
            }
        );
    }
}


/* ============================================================
   SUBJECT-WISE ATTENDANCE
   ============================================================ */

async function loadSubjectAttendance() {

    const subjects =
        await api(
            "/api/students/subject-attendance"
        );


    const wrap =
        document.getElementById("subjectCards");


    if (!wrap) {
        return;
    }


    const subjectList =
        Array.isArray(subjects)
            ? subjects
            : [];


    if (!subjectList.length) {

        wrap.innerHTML = `
            <p class="muted">
                No attendance recorded yet.
            </p>
        `;

        return;
    }


    wrap.innerHTML =
        subjectList.map(subject => {

            const total =
                Number(
                    subject.total_classes ??
                    subject.total ??
                    0
                );


            const attended =
                Number(
                    subject.classes_attended ??
                    subject.attended ??
                    0
                );


            const absent =
                Number(
                    subject.classes_absent ??
                    subject.absent ??
                    0
                );


            let percentage =
                Number(
                    subject.attendance_percentage ??
                    subject.percentage ??
                    0
                );


            if (
                total > 0 &&
                (
                    subject.attendance_percentage === undefined &&
                    subject.percentage === undefined
                )
            ) {

                percentage =
                    (attended / total) * 100;
            }


            percentage =
                Math.max(
                    0,
                    Math.min(
                        100,
                        Number(percentage.toFixed(2))
                    )
                );


            return `
                <div class="card">

                    <div
                        class="muted"
                        style="
                            font-weight:800;
                            font-size:.78rem;
                            letter-spacing:.5px
                        "
                    >
                        ${esc(
                            subject.subject_code || "-"
                        )}
                    </div>


                    <h3>
                        ${esc(
                            subject.subject_name ||
                            "Unknown Subject"
                        )}
                    </h3>


                    <div
                        class="progress"
                        style="margin:14px 0 10px"
                    >

                        <i
                            class="${pctClass(percentage)}"
                            style="width:${percentage}%"
                        ></i>

                    </div>


                    <div
                        style="
                            display:flex;
                            justify-content:space-between;
                            font-size:.88rem
                        "
                    >

                        <span class="muted">
                            Attended
                            <b>${attended}</b>
                            / ${total}
                        </span>


                        <span style="font-weight:800">
                            ${percentage}%
                        </span>

                    </div>


                    <div style="margin-top:10px">

                        <span
                            class="badge badge-present"
                        >
                            Present ${attended}
                        </span>


                        <span
                            class="badge badge-absent"
                        >
                            Absent ${absent}
                        </span>

                    </div>

                </div>
            `;

        }).join("");
}


/* ============================================================
   MONTHLY ATTENDANCE
   ============================================================ */

async function loadMonthly() {

    const months =
        await api(
            "/api/students/monthly-attendance"
        );


    const tbody =
        document.getElementById("monthlyBody");


    if (!tbody) {
        return;
    }


    const monthlyData =
        Array.isArray(months)
            ? months
            : [];


    if (!monthlyData.length) {

        tbody.innerHTML = `
            <tr>
                <td
                    colspan="5"
                    class="muted"
                >
                    No records found.
                </td>
            </tr>
        `;

        return;
    }


    tbody.innerHTML =
        monthlyData.map(month => {

            const total =
                Number(month.total || 0);

            const attended =
                Number(month.attended || 0);

            const absent =
                Number(month.absent || 0);


            let percentage =
                Number(month.percentage || 0);


            if (
                month.percentage === undefined
            ) {

                percentage =
                    total > 0
                        ? (attended / total) * 100
                        : 0;
            }


            percentage =
                Math.max(
                    0,
                    Math.min(
                        100,
                        Number(percentage.toFixed(2))
                    )
                );


            return `
                <tr>

                    <td>
                        ${esc(
                            month.month || "-"
                        )}
                    </td>


                    <td>
                        ${total}
                    </td>


                    <td>

                        <span
                            class="badge badge-present"
                        >
                            ${attended}
                        </span>

                    </td>


                    <td>

                        <span
                            class="badge badge-absent"
                        >
                            ${absent}
                        </span>

                    </td>


                    <td>

                        <div
                            style="
                                display:flex;
                                align-items:center;
                                gap:10px
                            "
                        >

                            <div
                                class="progress"
                                style="width:90px"
                            >

                                <i
                                    class="${pctClass(percentage)}"
                                    style="width:${percentage}%"
                                ></i>

                            </div>


                            <b>
                                ${percentage}%
                            </b>

                        </div>

                    </td>

                </tr>
            `;

        }).join("");
}


/* ============================================================
   PAGE ERROR
   ============================================================ */

function showPageError(message) {

    console.error(message);


    const possibleContainers = [
        document.getElementById("subjectList"),
        document.getElementById("subjectCards"),
        document.getElementById("recordsBody"),
        document.getElementById("monthlyBody")
    ];


    const container =
        possibleContainers.find(
            element => element
        );


    if (!container) {
        return;
    }


    if (container.tagName === "TBODY") {

        container.innerHTML = `
            <tr>
                <td
                    colspan="5"
                    class="muted"
                >
                    ${esc(message)}
                </td>
            </tr>
        `;

    } else {

        container.innerHTML = `
            <p class="muted">
                ${esc(message)}
            </p>
        `;
    }
}