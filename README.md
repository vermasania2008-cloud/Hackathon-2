# Roast Bud

Roast Bud is a playful AI code review studio built with Streamlit. Choose a response lens, paste code, and get feedback that can be savage, clean, investigative, or mentor-like.

## What is included

- Four response modes: Savage roast, Clean review, Bug hunter, and Mentor mode.
- Gemini API key fallback across `GEMINI_API_KEY_1` through `GEMINI_API_KEY_5`.
- SQLite and bcrypt authentication with sign up, sign in, and sign out.
- Cookie-backed login persistence so refreshes keep the user signed in.
- User-scoped SQLite review history with search, filters, sorting, and review details.
- Orange-and-white responsive UI with a branded sidebar and navigation.

## Setup

From the project folder, create or activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create `.env` values for Gemini. Add one or more keys; they are tried in order when a request fails:

```env
GEMINI_API_KEY_1=your_first_gemini_key
GEMINI_API_KEY_2=your_second_gemini_key
GEMINI_API_KEY_3=your_third_gemini_key
```

The legacy `GEMINI_API_KEY` variable is also supported as a final fallback.

## Run

```powershell
streamlit run roast_bud.py
```

Open the local URL printed by Streamlit. Create an account, sign in, choose a response lens, and submit code for review.

## Project map

- `roast_bud.py` - authenticated review experience and sidebar.
- `roast_bud_api.py` - Gemini prompts, response modes, and API key rotation.
- `pages/auth.py` - SQLite, bcrypt, and persistent cookie authentication helpers.
- `pages/history.py` - authenticated database-backed review history page.
- `style.css` - shared orange-and-white visual system.
- `.env` - local API keys; never commit this file.

## Notes

Review history and authentication data are local to this project. Login tokens are stored in the browser for 30 days and only hashed tokens are stored in the ignored `users.db` file. Reviews are stored per user in the same database.