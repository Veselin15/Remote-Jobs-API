import re
from .constants import (
    TECH_KEYWORDS, NEGATION_PATTERNS, SENIORITY_MAP,
    SALARY_IGNORE_TERMS, SALARY_HINTS, SALARY_MULTIPLIERS
)


def extract_skills(text):
    """
    Finds skills but ignores them if they appear near 'no experience' phrases.
    """
    if not text:
        return []

    found_skills = set()
    text_lower = text.lower()

    for skill in TECH_KEYWORDS:
        # Escape the skill for regex (e.g., C++)
        skill_esc = re.escape(skill.lower())
        pattern = r'\b' + skill_esc + r'\b'

        # C++ and C# handling
        if skill in ["C++", "C#", ".NET"]:
            pattern = re.escape(skill.lower())

        # Find all occurrences of the skill
        for match in re.finditer(pattern, text_lower):
            start, end = match.span()

            # Context Window: 50 chars before and 50 chars after
            context_start = max(0, start - 50)
            context_end = min(len(text_lower), end + 50)
            context_window = text_lower[context_start:context_end]

            # Check for negations in this window
            is_negative = False
            for neg in NEGATION_PATTERNS:
                if re.search(neg, context_window):
                    is_negative = True
                    break

            if not is_negative:
                found_skills.add(skill)
                # Once found valid, move to next skill
                break

    return list(found_skills)


def extract_seniority(title, description):
    """
    Determines seniority. Title has higher priority than description.
    """
    text_title = title.lower() if title else ""
    text_desc = description.lower() if description else ""

    # 1. Check Title First (Strongest Signal)
    for level, keywords in SENIORITY_MAP.items():
        for kw in keywords:
            if re.search(r'\b' + kw + r'\b', text_title):
                return level

    # 2. Check Description (Weaker Signal)
    for level, keywords in SENIORITY_MAP.items():
        for kw in keywords:
            if re.search(r'\b' + kw + r'\b', text_desc):
                return level

    # Default
    return "Not Specified"


def parse_salary(text):
    if not text: return None, None, None

    # 1. Detect Currency
    currency = "USD"
    if '€' in text or 'EUR' in text:
        currency = "EUR"
    elif '£' in text or 'GBP' in text:
        currency = "GBP"
    elif 'BGN' in text or 'lv' in text:
        currency = "BGN"

    text_lower = text.lower()
    clean_numbers = []

    # --- Helper: Detect Multiplier based on context ---
    def get_annual_multiplier(end_pos):
        # Look 30 chars ahead (e.g., "5000 per month")
        suffix = text_lower[end_pos:end_pos + 30]

        for period, patterns in SALARY_MULTIPLIERS.items():
            for pattern in patterns:
                if re.search(pattern, suffix):
                    if period == 'monthly': return 12
                    if period == 'hourly': return 2080  # 40hr * 52w
                    if period == 'daily': return 260  # 5d * 52w
                    if period == 'yearly': return 1
        return 1  # Default to yearly if unknown

    # --- Helper: Validator ---
    def is_valid_match(match_obj, has_k):
        start, end = match_obj.span()
        suffix = text_lower[end:end + 40]

        # 1. Ignore "250,000 users"
        if any(re.search(r'\b' + re.escape(term) + r'\b', suffix) for term in SALARY_IGNORE_TERMS):
            return False

        # 2. Accept if explicit currency, 'k' suffix, or salary keyword
        window = text_lower[max(0, start - 50):min(len(text_lower), end + 50)]
        if has_k: return True
        if any(s in text_lower[max(0, start - 5):end + 5] for s in ['$', '€', '£', 'bgn']): return True
        if any(re.search(r'\b' + h + r'\b', window) for h in SALARY_HINTS): return True

        return False

    # Strategy A: Ranges (80-100k)
    for m in re.finditer(r'(\d+)\s*[-–to]\s*(\d+)\s*[kK]', text_lower):
        if is_valid_match(m, True):
            mult = get_annual_multiplier(m.end())
            clean_numbers.extend([int(m.group(1)) * 1000 * mult, int(m.group(2)) * 1000 * mult])

    # Strategy B: Ranges without k (4000-5000 / month)
    if not clean_numbers:
        for m in re.finditer(r'(\d+)\s*[-–to]\s*(\d+)', text_lower):
            # Check if this range is followed by a period (e.g. /month)
            mult = get_annual_multiplier(m.end())
            # Only accept "naked" ranges if we found a period multiplier (implies it's a rate)
            if mult > 1 and is_valid_match(m, False):
                clean_numbers.extend([int(m.group(1)) * mult, int(m.group(2)) * mult])

    # Strategy C: Individual numbers
    if not clean_numbers:
        for m in re.finditer(r'(\d+[,\.]?\d*)\s*([kK])?', text_lower):
            val_str = m.group(1).replace(',', '').replace('.', '')
            if not val_str.isdigit(): continue

            val = float(val_str)
            has_k = (m.group(2) and m.group(2).lower() == 'k')
            if has_k: val *= 1000

            if is_valid_match(m, has_k):
                mult = get_annual_multiplier(m.end())
                annual_val = val * mult

                # Sanity Check (Annualized)
                if 15000 <= annual_val <= 500000:
                    clean_numbers.append(int(annual_val))

    if not clean_numbers: return None, None, None

    return min(clean_numbers), max(clean_numbers), currency