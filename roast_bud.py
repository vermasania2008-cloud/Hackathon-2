import streamlit as st
from pathlib import Path
from datetime import datetime
from roast_bud_api import RESPONSE_MODES, roast_code
from pages.auth import authentication_page, clear_authenticated_session, restore_authenticated_session, save_review

# Standard page configurations
st.set_page_config(
    page_title="ROAST BUD — Code Reviewer",

  layout="wide",
    initial_sidebar_state="expanded"
)

# Load the clean design architecture
css_path = Path(__file__).with_name("style.css")
logo_path = Path(__file__).with_name("images") / "logo.png"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

restore_authenticated_session()
if not st.session_state.get("authenticated", False):
  authentication_page()
  st.stop()

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
  st.page_link("pages/history.py", label="History", icon=":material/history:")

st.markdown(
  f"""
    <header class="topbar">
      <div class="brand-lockup">
        <div class="brand-mark">RB</div>
        <div>
          <div class="brand-name">Roast Bud</div>
          <div class="brand-status"><span></span> Online · Code reviewer</div>
        </div>
      </div>
      <div class="topbar-note">Brutal feedback. Useful fixes.</div>
    </header>
    <section class="welcome-block">
      <div class="eyebrow">YOUR PERSONAL CODE REVIEW BUDDY</div>
      <h1>Pick your lens.<br>Ship better code.</h1>
      <p>Drop code below and get a response that matches the moment: sharp, savage, surgical, or supportive.</p>
    </section>
    
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="mode-heading"><span>RESPONSE LENS</span><small>How should Roast Bud show up?</small></div>', unsafe_allow_html=True)
selected_mode = st.radio(
  "Response lens",
  list(RESPONSE_MODES),
  format_func=lambda mode: f"{mode}  ·  {RESPONSE_MODES[mode]['tagline']}",
  horizontal=True,
  label_visibility="collapsed",
)
st.markdown(f'<div class="mode-note"><span class="mode-pulse"></span><strong>{selected_mode}</strong><span> {RESPONSE_MODES[selected_mode]["tagline"]}</span></div>', unsafe_allow_html=True)


def render_review(result, review_key):
  if isinstance(result, str):
    st.markdown(result)
    return

  st.markdown(result.get("review", "Review completed."))
  st.markdown('<div class="feature-kicker">BEGINNER BREAKDOWN</div>', unsafe_allow_html=True)
  st.markdown(f'<div class="explanation-card"><strong>In plain English</strong><p>{result.get("beginner_summary", "Start with the suggested next move and test it with a small example.")}</p></div>', unsafe_allow_html=True)

  comments = result.get("comment_explanations", [])
  if comments:
    st.markdown('<div class="feature-kicker feature-gap">COMMENT TRANSLATOR</div>', unsafe_allow_html=True)
    comment_columns = st.columns(min(2, len(comments)))
    for index, comment in enumerate(comments):
      with comment_columns[index % len(comment_columns)]:
        st.markdown(f'<div class="comment-card"><code>{comment.get("comment", "Code comment")}</code><strong>What it means</strong><p>{comment.get("meaning", "This comment explains the nearby code.")}</p><small>{comment.get("why_it_matters", "It gives the next reader useful context.")}</small></div>', unsafe_allow_html=True)

  quiz = result.get("quiz")
  if quiz and quiz.get("options"):
    st.markdown('<div class="feature-kicker feature-gap">MINI CHECK</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-card"><strong>{quiz.get("question", "What is the main lesson from this review?")}</strong></div>', unsafe_allow_html=True)
    answer = st.radio("Quiz answer", quiz["options"], key=f"quiz_answer_{review_key}", label_visibility="collapsed")
    if st.button("Check answer", key=f"quiz_check_{review_key}"):
      selected_index = quiz["options"].index(answer)
      if selected_index == quiz.get("correct_index", 0):
        st.success("Correct. " + quiz.get("explanation", "You spotted the key idea."))
      else:
        st.error("Not quite. " + quiz.get("explanation", "Read the beginner breakdown and try again."))

with st.sidebar:
  sidebar_logo, sidebar_copy = st.columns([1, 3])
  with sidebar_logo:
    if logo_path.exists():
      st.image(str(logo_path), width=46)
  with sidebar_copy:
    st.markdown('<div class="sidebar-brand-copy"><strong>Roast Bud</strong><small>review cockpit</small></div>', unsafe_allow_html=True)
  st.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
  st.markdown('<div class="sidebar-kicker">NAVIGATION</div>', unsafe_allow_html=True)
  st.markdown('<a class="sidebar-nav-link" href="/">Review</a>', unsafe_allow_html=True)
  st.page_link("pages/history.py", label="Review history", icon=":material/history:")
  st.markdown('<div class="sidebar-kicker">ACTIVE LENS</div>', unsafe_allow_html=True)
  st.markdown(f'<div class="sidebar-lens"><span class="sidebar-lens-dot"></span><strong>{selected_mode}</strong><small>{RESPONSE_MODES[selected_mode]["tagline"]}</small></div>', unsafe_allow_html=True)
  st.markdown('<div class="sidebar-kicker sidebar-section-gap">THE LOOP</div>', unsafe_allow_html=True)
  st.markdown('<div class="sidebar-steps"><div><b>01</b><span>Drop your code</span></div><div><b>02</b><span>Choose your lens</span></div><div><b>03</b><span>Ship the fix</span></div></div>', unsafe_allow_html=True)
  review_count = len(st.session_state.get("review_history", []))
  st.markdown(f'<div class="sidebar-status"><span class="sidebar-status-dot"></span><div><strong>{review_count} reviews</strong><small>in this session</small></div></div>', unsafe_allow_html=True)
  user = st.session_state.get("user", {})
  st.markdown(f'<div class="sidebar-user"><span>{user.get("name", "Reviewer")[:1].upper()}</span><div><strong>{user.get("name", "Reviewer")}</strong><small>{user.get("email", "Signed in")}</small></div></div>', unsafe_allow_html=True)
  if st.button("Sign out", use_container_width=True):
    clear_authenticated_session()
    st.rerun()

if "messages" not in st.session_state:
  st.session_state.messages = []

for message in st.session_state.messages:
  with st.chat_message(message["role"], avatar="user" if message["role"] == "user" else ":material/auto_awesome:"):
    if message["role"] == "user":
      st.markdown(f"**{message.get('mode', 'Review')}** · code submitted")
      st.code(message["content"], language=message.get("language", "python"))
    else:
      render_review(message["content"], message.get("id", "history"))

user_code = st.chat_input("Paste code here and ask Roast Bud...")

if user_code:
  review_id = f"review_{len(st.session_state.messages)}"
  st.session_state.messages.append({"role": "user", "content": user_code, "language": "python", "mode": selected_mode})
  with st.chat_message("user", avatar="user"):
    st.markdown(f"**{selected_mode}** · code submitted")
    st.code(user_code, language="python")

  with st.chat_message("assistant", avatar="assistant"):
    with st.spinner("Bud is sharpening the roast..."):
      try:
        result = roast_code(user_code, selected_mode)
        render_review(result, review_id)
        st.session_state.messages.append({"role": "assistant", "content": result, "id": review_id})
        review_history = st.session_state.setdefault("review_history", [])
        review_text = result.get("review", "Review completed.") if isinstance(result, dict) else result
        review_history.append({
          "title": f"{selected_mode} · Python review",
          "repository": "Local workspace",
          "language": "Python",
          "status": "Needs attention",
          "summary": review_text.splitlines()[0] if review_text.splitlines() else "Review completed.",
          "findings": max(1, sum(review_text.lower().count(term) for term in ("fix", "risk", "bug", "issue")) // 2),
          "messages": 2,
          "branch": selected_mode.lower().replace(" ", "-"),
          "reviewer": "Roast Bud",
          "created_at": datetime.now(),
        })
        save_review(st.session_state.user["id"], review_history[-1])
      except Exception as error:
        st.error(f"Something went wrong: {error}")
