from datetime import datetime

import streamlit as st


st.set_page_config(page_title="Review history", layout="wide")

review_history = st.session_state.get("review_history", [])

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root { --ink: #17211b; --muted: #6e776f; --line: #dfe5df; --paper: #f8faf6; }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stMainBlockContainer"] { max-width: 1120px; padding-top: 42px; }
    h1, h2, h3, p, label, button, input, select { font-family: 'Space Grotesk', sans-serif !important; }
    h1 { letter-spacing: -0.04em; font-size: 2.7rem !important; margin-bottom: 0 !important; }
    .eyebrow { color: #738078; font-family: 'DM Mono', monospace; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 8px; }
    .subhead { color: var(--muted); font-size: 1rem; margin-top: 7px; }
    .metric-strip { display: flex; gap: 34px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); margin: 30px 0 22px; padding: 14px 0; }
    .metric { color: var(--muted); font-size: .82rem; }
    .metric strong { color: var(--ink); font-size: 1.05rem; margin-right: 4px; }
    .review-card { background: white; border: 1px solid var(--line); border-radius: 8px; padding: 17px 20px; margin: 10px 0; }
    .review-top { align-items: center; display: flex; gap: 10px; justify-content: space-between; }
    .review-title { color: var(--ink); font-size: 1.02rem; font-weight: 600; }
    .review-meta, .review-summary { color: var(--muted); font-size: .82rem; }
    .review-meta { margin-top: 5px; }
    .review-summary { line-height: 1.5; margin: 13px 0 2px; }
    .pill { border-radius: 99px; display: inline-block; font-size: .72rem; font-weight: 600; padding: 4px 9px; white-space: nowrap; }
    .resolved { background: #e7f5d2; color: #47721b; }
    .attention { background: #fff0d6; color: #8b5b0a; }
    .progress { background: #e5eef1; color: #326071; }
    .code { color: #66726a; font-family: 'DM Mono', monospace; font-size: .72rem; }
    .empty { border: 1px dashed #b9c5ba; border-radius: 8px; color: var(--muted); margin-top: 14px; padding: 42px; text-align: center; }
    @media (max-width: 650px) { h1 { font-size: 2.2rem !important; } .metric-strip { gap: 17px; } .review-top { align-items: flex-start; flex-direction: column; } }
    </style>
    """,
    unsafe_allow_html=True,
)

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
