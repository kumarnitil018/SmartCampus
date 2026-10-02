/* ============================================================
   script.js – shared helpers used by every page
   ============================================================ */

/* Small wrapper around fetch that always talks JSON and always sends
   the session cookie. Throws an Error with the server message on failure. */
async function api(path, options = {}) {
    const opts = Object.assign({ credentials: "same-origin", headers: {} }, options);
    if (opts.body && typeof opts.body !== "string") {
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { data = {}; }
    if (!res.ok) {
        throw new Error((data && data.error) || "Request failed (" + res.status + ")");
    }
    return data;
}

/* Toggle the mobile navigation menu on the landing page. */
function toggleNav() {
    const links = document.getElementById("navLinks");
    if (links) links.classList.toggle("open");
}

/* Toggle the sidebar on dashboard pages. */
function toggleSidebar() {
    const sb = document.getElementById("sidebar");
    if (sb) sb.classList.toggle("open");
}

/* Redirect to a login page if the visitor is not logged in with `role`.
   Returns the user object when access is allowed. */
async function requireRole(role) {
    try {
        const user = await api("/api/auth/me");
        if (role && user.role !== role) {
            window.location.href = "/login.html";
            return null;
        }
        return user;
    } catch (e) {
        window.location.href = "/login.html";
        return null;
    }
}

/* Log the user out and send them home. */
async function logout() {
    try { await api("/api/auth/logout", { method: "POST" }); } catch (e) {}
    window.location.href = "/index.html";
}

/* Return the CSS class used to colour a progress bar by percentage. */
function pctClass(pct) {
    if (pct >= 75) return "p-high";
    if (pct >= 50) return "p-mid";
    return "p-low";
}

/* Escape user-supplied text before injecting it into the DOM. */
function esc(str) {
    return String(str == null ? "" : str)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

/* Show a message inside an alert element. */
function showAlert(el, message, type = "error") {
    if (!el) return;
    el.textContent = message;
    el.className = "alert alert-" + type + " show";
}

/* Simple date formatter (YYYY-MM-DD -> DD Mon YYYY). */
function prettyDate(iso) {
    if (!iso) return "";
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return iso;
    return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/* Highlight the active sidebar link based on the current file name. */
function markActiveNav() {
    const here = location.pathname.split("/").pop();
    document.querySelectorAll(".sidebar nav a").forEach(a => {
        if (a.getAttribute("href") === here) a.classList.add("active");
    });
}
