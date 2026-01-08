import re
from .constants import TECH_KEYWORDS, NEGATION_PATTERNS, SENIORITY_MAP, SALARY_IGNORE_TERMS


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
    if not text:
        return None, None, None

    currency = "USD"
    if '€' in text or 'EUR' in text:
        currency = "EUR"
    elif '£' in text or 'GBP' in text:
        currency = "GBP"
    elif 'BGN' in text or 'lv' in text:
        currency = "BGN"

    text_lower = text.lower()
    clean_numbers = []

    # 1. STRICT VALIDATION HELPER
    def is_valid_salary_match(match_obj, number_value, has_k_suffix):
        start_pos, end_pos = match_obj.span()

        # A. LOOKAHEAD CHECK (Exclude "250,000+ registered users")
        # Look at the next 40 characters for any ignore terms
        suffix = text_lower[end_pos:end_pos + 40]
        for term in SALARY_IGNORE_TERMS:
            # Check if the ignore term appears anywhere in the next 40 chars
            # We use regex boundries \b to match whole words (e.g. "users")
            if re.search(r'\b' + re.escape(term) + r'\b', suffix):
                return False

        # B. CONTEXT CHECK (The "Strict" Rule)
        # If it has a 'k' (e.g. 80k), it's likely a salary. Accept it.
        if has_k_suffix:
            return True

        # If it matches a strict currency pattern explicitly near the number (e.g. $250,000)
        # We look 5 chars back and 5 chars forward for currency symbols
        local_window = text_lower[max(0, start_pos - 5):min(len(text), end_pos + 5)]
        if any(c in local_window for c in ['$', '€', '£', 'bgn', 'lv']):
            return True

        # If no 'k' and no currency symbol, we require a SALARY_HINT nearby (within 50 chars)
        # This kills "250,000 users" but keeps "Salary: 250,000"
        context_window = text_lower[max(0, start_pos - 50):min(len(text), end_pos + 50)]
        for hint in SALARY_HINTS:
            if re.search(r'\b' + re.escape(hint) + r'\b', context_window):
                return True

        # If it failed all checks, it's just a random number
        return False

    # Strategy A: Ranges (80-100k)
    matches_k_range = re.finditer(r'(\d+)\s*[-–to]\s*(\d+)\s*[kK]', text_lower)
    for m in matches_k_range:
        # Ranges with 'k' are usually safe, but we still run the basic ignore check
        if is_valid_salary_match(m, 0, has_k_suffix=True):
            n1 = int(m.group(1))
            n2 = int(m.group(2))
            clean_numbers.extend([n1 * 1000, n2 * 1000])

    # Strategy B: Individual numbers (60k, 60,000)
    if not clean_numbers:
        matches = re.finditer(r'(\d+[,\.]?\d*)\s*([kK])?', text_lower)
        for m in matches:
            num_str = m.group(1)
            suffix = m.group(2)
            has_k = (suffix and suffix.lower() == 'k')

            clean_str = num_str.replace(',', '').replace('.', '')
            if not clean_str.isdigit(): continue
            val = float(clean_str)

            if has_k: val *= 1000

            # Apply Strict Rules
            if not is_valid_salary_match(m, val, has_k_suffix=has_k):
                continue

            clean_numbers.append(int(val))

    if not clean_numbers:
        return None, None, None

    salary_min = min(clean_numbers)
    salary_max = max(clean_numbers) if len(clean_numbers) > 1 else salary_min

    return salary_min, salary_max, currency