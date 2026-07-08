"""Resume → job match scoring (skills keyword match).

Deterministic and offline: a job lists required skills/keywords; the resume
text is scanned and the score is (matched skills / total skills) × 100. No LLM
needed. Swap `score_resume` for an AI call later without changing callers.
"""
import re


def extract_text(f):
    """Best-effort plain text from an uploaded resume (PDF / text)."""
    if not f:
        return ""
    name = (getattr(f, "name", "") or "").lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            f.seek(0)
            reader = PdfReader(f)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        f.seek(0)
        raw = f.read()
        if isinstance(raw, bytes):
            for enc in ("utf-8", "latin-1"):
                try:
                    return raw.decode(enc)
                except Exception:
                    continue
            return ""
        return str(raw)
    except Exception:
        return ""


def parse_skills(text):
    """Split a required-skills blob (commas / newlines / semicolons) into terms."""
    return [t.strip() for t in re.split(r"[,\n;]+", text or "") if t.strip()]


def score_resume(resume_text, required_skills):
    """Return (pct, matched[], missing[]) matching skills as case-insensitive
    substrings of the resume text."""
    skills = parse_skills(required_skills)
    if not skills:
        return 0, [], []
    low = (resume_text or "").lower()
    matched = [s for s in skills if s.lower() in low]
    missing = [s for s in skills if s.lower() not in low]
    pct = round(len(matched) / len(skills) * 100)
    return pct, matched, missing
