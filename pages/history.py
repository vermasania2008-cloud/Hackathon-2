from datetime import datetime
from pathlib import Path

import streamlit as st

from pages.auth import authentication_page, clear_authenticated_session, load_reviews, restore_authenticated_session


st.set_page_config(page_title="Review history", layout="wide", initial_sidebar_state="expanded")

css_path = Path(__file__).parents[1] / "style.css"
logo_path = css_path.parent / "images" / "logo.png"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

restore_authenticated_session()
if not st.session_state.get("authenticated", False):
    authentication_page()
    st.stop()

review_history = load_reviews(st.session_state.user["id"])

nav_brand, nav_review, nav_history = st.columns([5, 1, 1])
with nav_brand:
    logo_col, brand_col = st.columns([1, 4])
    with logo_col:
        if logo_path.exists():
            st.image(str(logo_path), width=44)
    with brand_col:
        st.markdown('<div class="nav-brand-copy"><strong>Roast Bud</strong><small>code review studio</small></div>', unsafe_allow_html=True)
with nav_review:
    st.markdown('<a class="nav-link" href="/">Review</a>', unsafe_allow_html=True)
with nav_history:
    st.markdown('<a class="nav-link" href="/history">History</a>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-kicker">NAVIGATION</div>', unsafe_allow_html=True)
    st.markdown('<a class="sidebar-nav-link" href="/">Review</a>', unsafe_allow_html=True)
    st.markdown('<a class="sidebar-nav-link sidebar-nav-active" href="/history">Review history</a>', unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        clear_authenticated_session()
        st.rerun()

st.markdown('<div class="eyebrow">Code review workspace</div>', unsafe_allow_html=True)
st.title("Review history")
st.markdown('<div class="subhead">A quiet record of the conversations behind your code.</div>', unsafe_allow_html=True)

total_findings = sum(review.get("findings", 0) for review in review_history)
latest_review = max(review_history, key=lambda review: review.get("created_at", datetime.min), default=None)
latest_label = latest_review["created_at"].strftime("%b %d") if latest_review else "-"
st.markdown(
    f'<div class="metric-strip"><div class="metric"><strong>{len(review_history)}</strong> reviews</div>'
    f'<div class="metric"><strong>{total_findings}</strong> findings</div>'
    f'<div class="metric"><strong>{latest_label}</strong> latest review</div></div>',
    unsafe_allow_html=True,
)

filter_col, status_col, language_col, sort_col = st.columns([2.1, 1.2, 1.2, 1.5])
with filter_col:
    search = st.text_input("Search", placeholder="Search reviews or repositories", label_visibility="collapsed")
with status_col:
    status_filter = st.selectbox("Status", ["All statuses", "In progress", "Needs attention", "Resolved"], label_visibility="collapsed")
with language_col:
    languages = sorted({review.get("language", "") for review in review_history if review.get("language")})
    language_filter = st.selectbox("Language", ["All languages", *languages], label_visibility="collapsed")
with sort_col:
    sort_order = st.selectbox("Sort", ["Oldest first", "Newest first", "Most findings", "Title A-Z"], label_visibility="collapsed")

filtered_reviews = [
    review for review in review_history
    if (not search or search.lower() in f'{review.get("title", "")} {review.get("repository", "")} {review.get("branch", "")}'.lower())
    and (status_filter == "All statuses" or review.get("status") == status_filter)
    and (language_filter == "All languages" or review.get("language") == language_filter)
]

if sort_order == "Newest first":
    filtered_reviews.sort(key=lambda review: review.get("created_at", datetime.min), reverse=True)
elif sort_order == "Most findings":
    filtered_reviews.sort(key=lambda review: review.get("findings", 0), reverse=True)
elif sort_order == "Title A-Z":
    filtered_reviews.sort(key=lambda review: review.get("title", "").lower())
else:
    filtered_reviews.sort(key=lambda review: review.get("created_at", datetime.min))

st.caption(f"{len(filtered_reviews)} of {len(review_history)} conversations")
if not filtered_reviews:
    st.markdown('<div class="empty">No review history is available yet.</div>', unsafe_allow_html=True)
else:
    for review in filtered_reviews:
        status_class = {"Resolved": "resolved", "Needs attention": "attention", "In progress": "progress"}.get(review.get("status"), "progress")
        created_at = review.get("created_at")
        created_label = created_at.strftime("%b %d, %Y at %H:%M") if created_at else "Date unavailable"
        st.markdown(
            f'<div class="review-card"><div class="review-top"><div><div class="review-title">{review.get("title", "Untitled review")}</div>'
            f'<div class="review-meta">{review.get("repository", "Repository unavailable")} · {review.get("language", "Language unavailable")} · {created_label}</div></div>'
            f'<span class="pill {status_class}">{review.get("status", "Unknown status")}</span></div>'
            f'<div class="review-summary">{review.get("summary", "No summary available.")}</div>'
            f'<span class="code">{review.get("findings", 0)} findings · {review.get("messages", 0)} messages · {review.get("branch", "Branch unavailable")}</span></div>',
            unsafe_allow_html=True,
        )
        with st.expander("View conversation details", expanded=False):
            st.write(f'**Reviewer:** {review.get("reviewer", "Unavailable")}')
            st.write(f'**Review date:** {created_label}')
            st.write(review.get("summary", "No summary available."))
