import streamlit as st
import sqlite3
import bcrypt
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from streamlit_cookies_controller import CookieController


# ============================================================
# DATABASE
# ============================================================

DB_NAME = str(Path(__file__).parents[1] / "users.db")
AUTH_COOKIE = "roast_bud_session"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24 * 30


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_users_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    user_columns = {row[1] for row in cursor.execute("PRAGMA table_info(users)")}
    if "session_token_hash" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN session_token_hash TEXT")
    if "session_token_expires_at" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN session_token_expires_at TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            repository TEXT,
            language TEXT,
            status TEXT,
            summary TEXT,
            findings INTEGER DEFAULT 0,
            messages INTEGER DEFAULT 0,
            branch TEXT,
            reviewer TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _set_authenticated_user(user):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(seconds=AUTH_COOKIE_MAX_AGE)
    conn = get_connection()
    conn.execute(
        "UPDATE users SET session_token_hash = ?, session_token_expires_at = ? WHERE id = ?",
        (_token_hash(token), expires_at.isoformat(), user["id"]),
    )
    conn.commit()
    conn.close()
    CookieController().set(AUTH_COOKIE, token, max_age=AUTH_COOKIE_MAX_AGE, same_site="lax")
    st.session_state.authenticated = True
    st.session_state.user = user
    st.session_state.auth_token = token


def restore_authenticated_session():
    create_users_table()
    if st.session_state.get("authenticated", False):
        return True

    token = CookieController().get(AUTH_COOKIE)
    if not token:
        return False

    conn = get_connection()
    user = conn.execute(
        "SELECT id, name, email, session_token_expires_at FROM users WHERE session_token_hash = ?",
        (_token_hash(token),),
    ).fetchone()
    conn.close()
    if not user or not user[3] or datetime.fromisoformat(user[3]) <= datetime.utcnow():
        CookieController().remove(AUTH_COOKIE)
        return False

    st.session_state.authenticated = True
    st.session_state.user = {"id": user[0], "name": user[1], "email": user[2]}
    st.session_state.auth_token = token
    return True


def clear_authenticated_session():
    token = st.session_state.get("auth_token")
    if token:
        conn = get_connection()
        conn.execute("UPDATE users SET session_token_hash = NULL, session_token_expires_at = NULL WHERE session_token_hash = ?", (_token_hash(token),))
        conn.commit()
        conn.close()
    CookieController().remove(AUTH_COOKIE)
    st.session_state.authenticated = False
    st.session_state.pop("auth_token", None)
    st.session_state.pop("user", None)


def save_review(user_id, review):
    conn = get_connection()
    conn.execute(
        """INSERT INTO reviews (user_id, title, repository, language, status, summary, findings, messages, branch, reviewer, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, review["title"], review["repository"], review["language"], review["status"], review["summary"], review["findings"], review["messages"], review["branch"], review["reviewer"], review["created_at"].isoformat()),
    )
    conn.commit()
    conn.close()


def load_reviews(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT title, repository, language, status, summary, findings, messages, branch, reviewer, created_at FROM reviews WHERE user_id = ? ORDER BY created_at ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    fields = ["title", "repository", "language", "status", "summary", "findings", "messages", "branch", "reviewer", "created_at"]
    reviews = []
    for row in rows:
        review = dict(zip(fields, row))
        review["created_at"] = datetime.fromisoformat(review["created_at"])
        reviews.append(review)
    return reviews


# ============================================================
# VALIDATION
# ============================================================

def valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def valid_password(password):
    """Password must be strong enough for account creation."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


def password_strength(password):
    if not password:
        return {"score": 0, "label": "No password yet", "checks": [False, False, False, False]}

    checks = [
        len(password) >= 8,
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
    ]
    score = sum(checks)

    if score <= 1:
        label = "Very weak"
    elif score == 2:
        label = "Weak"
    elif score == 3:
        label = "Good"
    else:
        label = "Strong"

    return {"score": score, "label": label, "checks": checks}


# ============================================================
# SIGN UP
# ============================================================

def signup_user(name, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = hash_password(password)

    try:

        cursor.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))

        conn.commit()
        conn.close()

        return True, "Account created successfully."

    except sqlite3.IntegrityError:

        conn.close()

        return False, "An account with this email already exists."


# ============================================================
# LOGIN
# ============================================================

def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, password
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    conn.close()

    if user is None:
        return False, None

    user_id, name, email, hashed_password = user

    if verify_password(password, hashed_password):

        return True, {
            "id": user_id,
            "name": name,
            "email": email
        }

    return False, None


def get_user_by_email(email):
    conn = get_connection()
    user = conn.execute("SELECT id, name, email FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return {"id": user[0], "name": user[1], "email": user[2]} if user else None


# ============================================================
# LOGIN PAGE UI
# ============================================================

def authentication_page():
    create_users_table()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    css_path = Path(__file__).parents[1] / "style.css"
    logo_path = css_path.parent / "images" / "logo.png"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

    title_column, logo_column = st.columns([1.45, 1], gap="large")
    with title_column:
        st.markdown(
            '<div class="auth-copy-block"><div class="auth-eyebrow">PRIVATE CODE REVIEW STUDIO</div><h1 class="auth-title">Welcome back,<br><em>Roast Bud.</em></h1><p class="auth-copy">Sign in to roast bugs, keep your review trail, and ship the next fix with a little more confidence.</p></div>',
            unsafe_allow_html=True,
        )
    with logo_column:
        if logo_path.exists():
            st.image(str(logo_path), width=240)

    login_tab, signup_tab = st.tabs(["Sign In", "Create Account"])

    with login_tab:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Sign In")

            if submitted:
                if not email or not password:
                    st.error("Please enter your email and password.")
                elif not valid_email(email):
                    st.error("Please enter a valid email address.")
                else:
                    success, user = login_user(email.strip().lower(), password)
                    if success:
                        _set_authenticated_user(user)
                        st.success(f"Welcome, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

    with signup_tab:
        with st.form("signup_form", clear_on_submit=False):
            name = st.text_input("Full Name", placeholder="Jane Doe")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Minimum 8 chars")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

            if password:
                strength = password_strength(password)
                st.progress(min(1.0, strength["score"] / 4))
                st.caption(f"Password strength: {strength['label']}")

            submitted = st.form_submit_button("Create Account")

            if submitted:
                if not name or not email or not password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif not valid_email(email):
                    st.error("Please enter a valid email address.")
                elif not valid_password(password):
                    st.error("Password must include 8+ characters, uppercase, lowercase, and a number.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = signup_user(name.strip(), email.strip().lower(), password)
                    if success:
                        user = get_user_by_email(email.strip().lower())
                        _set_authenticated_user(user)
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)


if __name__ == "__main__":
    st.set_page_config(
        page_title="RoastBud",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    authentication_page()