/* ============================================================
   teacher.js – powers all pages inside /teacher/
   Dispatches to a loader based on <body data-page="...">.
   ============================================================ */

document.addEventListener("DOMContentLoaded", async () => {
    const user = await requireRole("teacher");

    if (!user) return;

    markActiveNav();

    const nameEl = document.getElementById("userName");

    if (nameEl) {
        nameEl.textContent = user.username;
    }

    const page = document.body.dataset.page;

    if (page === "dashboard") {
        await loadDashboard();
    }

    if (page === "subjects") {
        await loadSubjects();
    }

    if (page === "mark") {
        await loadMarkPage();
    }

    if (page === "history") {
        await loadHistoryPage();
    }
});


/* ============================================================
   Teacher Dashboard
   ============================================================ */

async function loadDashboard() {

    try {

        /*
         * IMPORTANT:
         * Backend routes are /api/teachers/...
         */

        const profile = await api("/api/teachers/profile");

        const subjects = await api("/api/teachers/subjects");


        /* ---------------- Teacher profile ---------------- */

        const teacherName = document.getElementById("teacherName");

        const deptInfo = document.getElementById("deptInfo");

        if (teacherName) {
            teacherName.textContent =
                profile.full_name || profile.username || "Teacher";
        }

        if (deptInfo) {

            const department =
                profile.department || "Department";

            const employeeId =
                profile.employee_id || "N/A";

            deptInfo.textContent =
                `${department} • Employee ID ${employeeId}`;
        }


        /* ---------------- Count students ---------------- */

        let totalStudents = 0;

        for (const subject of subjects) {

            try {

                const data = await api(
                    `/api/teachers/subjects/${subject.id}/students`
                );

                if (data && Array.isArray(data.students)) {
                    totalStudents += data.students.length;
                }

            } catch (error) {

                console.error(
                    `Could not load students for subject ${subject.id}:`,
                    error
                );

            }
        }


        /* ---------------- Statistics ---------------- */

        const statSubjects =
            document.getElementById("statSubjects");

        const statStudents =
            document.getElementById("statStudents");

        if (statSubjects) {
            statSubjects.textContent = subjects.length;
        }

        if (statStudents) {
            statStudents.textContent = totalStudents;
        }


        /* ---------------- Subject cards ---------------- */

        const wrap =
            document.getElementById("subjectCards");

        if (!wrap) {
            return;
        }


        if (!subjects.length) {

            wrap.innerHTML = `
                <p class="muted">
                    You have no subjects yet.
                    <a
                        href="subjects.html"
                        style="color:var(--t-accent);font-weight:700"
                    >
                        Add one →
                    </a>
                </p>
            `;

            return;
        }


        wrap.innerHTML = subjects.map(subject => `

            <div class="subject-card">

                <div class="code">
                    ${esc(subject.subject_code)}
                </div>

                <h3>
                    ${esc(subject.subject_name)}
                </h3>

                <div class="meta">
                    ${esc(subject.course)}
                    •
                    ${esc(subject.branch)}
                    •
                    Sem ${subject.semester}
                </div>

                <div class="actions">

                    <a
                        href="mark-attendance.html?subject=${subject.id}"
                        style="
                            background:var(--t-accent);
                            color:#fff
                        "
                    >
                        Take Attendance
                    </a>

                    <a
                        href="attendance-history.html?subject=${subject.id}"
                        style="
                            background:var(--t-accent-light);
                            color:var(--t-accent-dark)
                        "
                    >
                        History
                    </a>

                </div>

            </div>

        `).join("");

    } catch (error) {

        console.error(
            "Teacher dashboard error:",
            error
        );

        const wrap =
            document.getElementById("subjectCards");

        if (wrap) {

            wrap.innerHTML = `
                <p class="muted">
                    Unable to load teacher dashboard.
                </p>
            `;

        }

    }
}


/* ============================================================
   Subject Management
   ============================================================ */

async function loadSubjects() {

    const mine =
        await api("/api/teachers/subjects");

    const available =
        await api("/api/teachers/available-subjects");


    const wrap =
        document.getElementById("mySubjects");


    if (wrap) {

        wrap.innerHTML = mine.length

            ? mine.map(subject => `

                <div class="subject-card">

                    <div class="code">
                        ${esc(subject.subject_code)}
                    </div>

                    <h3>
                        ${esc(subject.subject_name)}
                    </h3>

                    <div class="meta">
                        ${esc(subject.course)}
                        •
                        ${esc(subject.branch)}
                        •
                        Sem ${subject.semester}
                    </div>

                    <div class="actions">

                        <a
                            href="mark-attendance.html?subject=${subject.id}"
                            style="
                                background:var(--t-accent);
                                color:#fff
                            "
                        >
                            Take Attendance
                        </a>

                        <button
                            data-id="${subject.id}"
                            class="remove-btn"
                            style="
                                background:var(--danger-light);
                                color:var(--danger)
                            "
                        >
                            Remove
                        </button>

                    </div>

                </div>

            `).join("")

            : `<p class="muted">No subjects yet.</p>`;


        wrap.querySelectorAll(".remove-btn")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    async () => {

                        if (
                            !confirm(
                                "Remove this subject from your list?"
                            )
                        ) {
                            return;
                        }

                        await api(
                            `/api/teachers/subjects/${button.dataset.id}`,
                            {
                                method: "DELETE"
                            }
                        );

                        loadSubjects();

                    }
                );

            });

    }


    /* ---------------- Available subjects ---------------- */

    const select =
        document.getElementById("assignSelect");

    if (select) {

        select.innerHTML = `
            <option value="">
                Select a subject…
            </option>
        ` +

        available.map(subject => `

            <option value="${subject.id}">
                ${esc(subject.subject_code)}
                –
                ${esc(subject.subject_name)}
            </option>

        `).join("");

    }


    /* ---------------- Assign existing subject ---------------- */

    const assignButton =
        document.getElementById("assignBtn");

    if (assignButton) {

        assignButton.onclick = async () => {

            const alertBox =
                document.getElementById("alertBox");

            if (!select.value) {

                return showAlert(
                    alertBox,
                    "Please choose a subject.",
                    "error"
                );

            }

            try {

                await api(
                    "/api/teachers/subjects/assign",
                    {
                        method: "POST",
                        body: {
                            subject_id:
                                Number(select.value)
                        }
                    }
                );

                showAlert(
                    alertBox,
                    "Subject assigned!",
                    "success"
                );

                loadSubjects();

            } catch (error) {

                showAlert(
                    alertBox,
                    error.message,
                    "error"
                );

            }

        };

    }


    /* ---------------- Create new subject ---------------- */

    const form =
        document.getElementById("newSubjectForm");

    if (form) {

        form.onsubmit = async event => {

            event.preventDefault();

            const alertBox =
                document.getElementById("alertBox");


            const payload = {

                subject_code:
                    form.subject_code.value.trim(),

                subject_name:
                    form.subject_name.value.trim(),

                course:
                    form.course.value.trim(),

                branch:
                    form.branch.value.trim(),

                semester:
                    form.semester.value

            };


            try {

                await api(
                    "/api/teachers/subjects",
                    {
                        method: "POST",
                        body: payload
                    }
                );

                showAlert(
                    alertBox,
                    "Subject created and assigned to you!",
                    "success"
                );

                form.reset();

                loadSubjects();

            } catch (error) {

                showAlert(
                    alertBox,
                    error.message,
                    "error"
                );

            }

        };

    }

}


/* ============================================================
   Mark Attendance
   ============================================================ */

let markState = {
    subjectId: null,
    date: null,
    students: [],
    statuses: {}
};


async function loadMarkPage() {

    const subjects =
        await api("/api/teachers/subjects");


    const select =
        document.getElementById("subjectSelect");


    select.innerHTML = `
        <option value="">
            Select subject…
        </option>
    ` +

    subjects.map(subject => `

        <option value="${subject.id}">
            ${esc(subject.subject_code)}
            –
            ${esc(subject.subject_name)}
        </option>

    `).join("");


    const dateInput =
        document.getElementById("dateInput");


    dateInput.value =
        new Date()
            .toISOString()
            .slice(0, 10);


    /* ---------------- URL subject ---------------- */

    const params =
        new URLSearchParams(location.search);


    if (params.get("subject")) {
        select.value =
            params.get("subject");
    }


    select.addEventListener(
        "change",
        refreshStudents
    );


    dateInput.addEventListener(
        "change",
        refreshStudents
    );


    document
        .getElementById("saveBtn")
        .addEventListener(
            "click",
            saveAttendance
        );


    document
        .getElementById("markAllPresent")
        .addEventListener(
            "click",
            () => setAll("Present")
        );


    document
        .getElementById("markAllAbsent")
        .addEventListener(
            "click",
            () => setAll("Absent")
        );


    if (select.value) {
        refreshStudents();
    }

}


async function refreshStudents() {

    const subjectId =
        document.getElementById(
            "subjectSelect"
        ).value;


    const date =
        document.getElementById(
            "dateInput"
        ).value;


    const list =
        document.getElementById(
            "studentList"
        );


    if (!subjectId || !date) {

        list.innerHTML = `
            <p class="muted">
                Choose a subject and date.
            </p>
        `;

        return;

    }


    const data =
        await api(
            `/api/teachers/subjects/${subjectId}/students`
        );


    const existing =
        await api(
            `/api/attendance/subject/${subjectId}/date/${date}`
        );


    const existingMap = {};


    existing.forEach(record => {

        existingMap[
            record.student_id
        ] = record.status;

    });


    markState = {

        subjectId,

        date,

        students:
            data.students,

        statuses: {}

    };


    data.students.forEach(student => {

        markState.statuses[student.id] =
            existingMap[student.id]
            || "Present";

    });


    if (!data.students.length) {

        list.innerHTML = `
            <p class="muted">
                No students found for
                ${esc(data.subject.course)}
                ${esc(data.subject.branch)}
                Sem ${data.subject.semester}.
            </p>
        `;

        return;

    }


    renderStudentRows();

}


function renderStudentRows() {

    const list =
        document.getElementById(
            "studentList"
        );


    list.innerHTML =
        markState.students.map(student => {

            const status =
                markState.statuses[
                    student.id
                ];


            return `

                <div class="student-row">

                    <div class="roll">
                        ${esc(student.roll_number)}
                    </div>

                    <div class="nm">
                        ${esc(student.full_name)}
                    </div>

                    <div
                        class="muted"
                        style="font-size:.85rem"
                    >
                        ${esc(student.course)}
                        •
                        ${esc(student.branch)}
                    </div>

                    <div class="toggle">

                        <button
                            class="present ${
                                status === "Present"
                                    ? "active"
                                    : ""
                            }"
                            data-id="${student.id}"
                            data-status="Present"
                        >
                            Present
                        </button>

                        <button
                            class="absent ${
                                status === "Absent"
                                    ? "active"
                                    : ""
                            }"
                            data-id="${student.id}"
                            data-status="Absent"
                        >
                            Absent
                        </button>

                    </div>

                </div>

            `;

        }).join("");


    list
        .querySelectorAll(".toggle button")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const id =
                        Number(button.dataset.id);

                    markState.statuses[id] =
                        button.dataset.status;


                    const row =
                        button.closest(
                            ".student-row"
                        );


                    row
                        .querySelectorAll(
                            ".toggle button"
                        )
                        .forEach(
                            btn =>
                                btn.classList.remove(
                                    "active"
                                )
                        );


                    button.classList.add(
                        "active"
                    );

                }
            );

        });

}


function setAll(status) {

    markState.students.forEach(student => {

        markState.statuses[
            student.id
        ] = status;

    });

    renderStudentRows();

}


async function saveAttendance() {

    const alertBox =
        document.getElementById(
            "alertBox"
        );


    if (!markState.subjectId) {

        return showAlert(
            alertBox,
            "Select a subject first.",
            "error"
        );

    }


    const records =
        markState.students.map(student => ({

            student_id:
                student.id,

            status:
                markState.statuses[
                    student.id
                ]

        }));


    if (!records.length) {

        return showAlert(
            alertBox,
            "No students to save.",
            "error"
        );

    }


    try {

        const response =
            await api(
                "/api/attendance/mark",
                {
                    method: "POST",

                    body: {
                        subject_id:
                            Number(
                                markState.subjectId
                            ),

                        date:
                            markState.date,

                        records:
                            records
                    }
                }
            );


        showAlert(
            alertBox,
            response.message,
            "success"
        );

    } catch (error) {

        showAlert(
            alertBox,
            error.message,
            "error"
        );

    }

}


/* ============================================================
   Attendance History + Report
   ============================================================ */

async function loadHistoryPage() {

    const subjects =
        await api(
            "/api/teachers/subjects"
        );


    const select =
        document.getElementById(
            "subjectSelect"
        );


    select.innerHTML = `
        <option value="">
            Select subject…
        </option>
    ` +

    subjects.map(subject => `

        <option value="${subject.id}">
            ${esc(subject.subject_code)}
            –
            ${esc(subject.subject_name)}
        </option>

    `).join("");


    const params =
        new URLSearchParams(location.search);


    if (params.get("subject")) {

        select.value =
            params.get("subject");

    }


    select.addEventListener(
        "change",
        loadHistoryData
    );


    if (select.value) {

        loadHistoryData();

    }

}


async function loadHistoryData() {

    const subjectId =
        document.getElementById(
            "subjectSelect"
        ).value;


    if (!subjectId) {
        return;
    }


    const data =
        await api(
            `/api/teachers/subjects/${subjectId}/history`
        );


    const report =
        await api(
            `/api/teachers/subjects/${subjectId}/report`
        );


    /* ---------------- History table ---------------- */

    const historyBody =
        document.getElementById(
            "historyBody"
        );


    historyBody.innerHTML =
        data.records.length

        ? data.records.map(record => `

            <tr>

                <td>
                    ${prettyDate(record.date)}
                </td>

                <td>
                    ${esc(record.roll_number)}
                </td>

                <td>
                    ${esc(record.full_name)}
                </td>

                <td>

                    <span
                        class="
                            badge
                            badge-${
                                record.status === "Present"
                                    ? "present"
                                    : "absent"
                            }
                        "
                    >
                        ${record.status}
                    </span>

                </td>

            </tr>

        `).join("")

        : `
            <tr>
                <td
                    colspan="4"
                    class="muted"
                >
                    No attendance recorded yet.
                </td>
            </tr>
        `;


    /* ---------------- Report table ---------------- */

    const reportBody =
        document.getElementById(
            "reportBody"
        );


    reportBody.innerHTML =
        report.report.length

        ? report.report.map(record => `

            <tr>

                <td>
                    ${esc(record.roll_number)}
                </td>

                <td>
                    ${esc(record.full_name)}
                </td>

                <td>
                    ${record.total}
                </td>

                <td>
                    ${record.attended}
                </td>

                <td>
                    ${record.absent}
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
                                class="${pctClass(
                                    record.percentage
                                )}"
                                style="
                                    width:${record.percentage}%
                                "
                            ></i>

                        </div>

                        <b>
                            ${record.percentage}%
                        </b>

                    </div>

                </td>

            </tr>

        `).join("")

        : `
            <tr>
                <td
                    colspan="6"
                    class="muted"
                >
                    No data yet.
                </td>
            </tr>
        `;

}