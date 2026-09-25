import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

RESPONSE_MODES = {
    "Savage roast": {
        "tagline": "Hinglish heat + one useful fix",
        "prompt": "Be a sassy, savage but lovable Indian senior in Hinglish. Open with a short Gen-Z roast, then give one specific fix. Keep it punchy and funny.",
        "format": "Use: a 1-2 line roast, then 'Real talk:' with one actionable fix, then 'Code health:' with a rating out of 10 and a playful label.",
    },
    "Clean review": {
        "tagline": "Senior-level feedback, zero noise",
        "prompt": "Act like a sharp, kind senior engineer. Be direct, specific, and practical. Focus on correctness, maintainability, and the highest-impact change.",
        "format": "Use: 'What works', 'Risk', and 'Next move'. Keep each section concise and include a small rating out of 10.",
    },
    "Bug hunter": {
        "tagline": "Find the edge case before prod does",
        "prompt": "Act like a relentless debugging detective. Trace the code mentally, identify the most likely failure or edge case, and explain why it happens without inventing runtime facts.",
        "format": "Use: 'The suspect', 'Why it breaks', and 'Patch it'. Include a tiny input/output example when useful.",
    },
    "Mentor mode": {
        "tagline": "Learn the why, not just the fix",
        "prompt": "Act like an encouraging coding mentor. Explain the idea in simple language, teach the principle behind the issue, and give a safer improved direction.",
        "format": "Use: 'The idea', 'What your code is doing', and 'Try this next'. End with one question that helps the learner think.",
    },
}


def _configured_api_keys():
    numbered_keys = [
        os.getenv(f"GEMINI_API_KEY_{index}", "").strip()
        for index in range(1, 6)
    ]
    legacy_key = os.getenv("GEMINI_API_KEY", "").strip()
    return [key for key in (*numbered_keys, legacy_key) if key]


def _parse_review_response(response_text):
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        payload = json.loads(cleaned.strip())
    except json.JSONDecodeError:
        return {
            "review": response_text,
            "beginner_summary": "Read the review above first, then apply the suggested next move one step at a time.",
            "comment_explanations": [],
            "quiz": None,
        }

    payload.setdefault("review", "Review completed.")
    payload.setdefault("beginner_summary", "Start with the suggested next move and test it with a small example.")
    payload.setdefault("comment_explanations", [])
    payload.setdefault("quiz", None)
    return payload


def roast_code(code, mode="Savage roast"):
    api_keys = _configured_api_keys()
    if not api_keys:
        raise RuntimeError("No Gemini API keys are configured. Add GEMINI_API_KEY_1 to your .env file.")

    selected_mode = RESPONSE_MODES.get(mode, RESPONSE_MODES["Savage roast"])
    system_prompt = f"""
You are Roast Bud, a cool and helpful code reviewer.
{selected_mode['prompt']}
{selected_mode['format']}
Use emojis sparingly. Never claim to have run the code. Do not give a rating if the input is not code; ask for valid code instead.

Return ONLY valid JSON with this exact shape:
{{
    "review": "Your mode-specific response in beginner-friendly language.",
    "beginner_summary": "Explain the main idea like the reader is new to programming.",
    "comment_explanations": [
        {{"comment": "The exact code comment", "meaning": "What it says in simple words", "why_it_matters": "Why this comment helps"}}
    ],
    "quiz": {{"question": "One question based on this review", "options": ["A", "B", "C"], "correct_index": 0, "explanation": "Why the answer is correct"}}
}}
Explain EVERY comment present in the submitted code. If there are no comments, return an empty comment_explanations list and make the quiz test the main review idea.
"""
    last_error = None
    for api_key in api_keys:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"{system_prompt}\n\nReview this {mode} request:\n{code}"
            )
            return _parse_review_response(response.text)
        except Exception as error:
            last_error = error

    raise RuntimeError(
        f"All {len(api_keys)} configured Gemini API key(s) failed. Last error: {last_error}"
    ) from last_error


if __name__ == "__main__":
    test_code = input("Paste your code: ")
    print(roast_code(test_code))