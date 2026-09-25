
import streamlit as st
import sqlite3
import bcrypt
import re


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "users.db"


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


# ============================================================
# LOGIN PAGE UI
# ============================================================

def authentication_page():
    create_users_table()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    st.set_page_config(
        page_title="RoastBud",
        page_icon="🔥",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    st.title("RoastBud")

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
                        st.session_state.authenticated = True
                        st.session_state.user = user
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
                        st.success(message)
                        st.session_state.authenticated = True
                        st.session_state.user = {"name": name.strip(), "email": email.strip().lower()}
                        st.rerun()
                    else:
                        st.error(message)


if __name__ == "__main__":
    authentication_page()

