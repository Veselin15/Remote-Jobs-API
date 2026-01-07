import re

# 1. Define the Skills List
TECH_KEYWORDS = [
    "Python", "Django", "Flask", "FastAPI", "React", "Angular", "Vue", "Node.js",
    "JavaScript", "TypeScript", "HTML", "CSS", "SQL", "PostgreSQL", "MySQL",
    "Redis", "MongoDB", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux",
    "Git", "CI/CD", "Machine Learning", "AI", "Data Science", "Pandas", "NumPy",
    "Scikit-learn", "TensorFlow", "PyTorch", "Celery", "RabbitMQ", "GraphQL",
    "REST API", "DevOps", "Terraform", "Ansible", "C++", "Java", "Go", "Rust", "Ruby"
]


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
        if skill in ["C++", "C#"]:
            pattern = re.escape(skill.lower())

        # Find all occurrences of the skill
        for match in re.finditer(pattern, text_lower):
            start, end = match.span()

            # Context Window: 50 chars before and 50 chars after
            # This lets us see "no experience with Java"
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
                # Once found valid, move to next skill (no need to check other matches of same skill)
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

    # Identify Currency
    currency = "USD"
    if '€' in text or 'EUR' in text:
        currency = "EUR"
    elif '£' in text or 'GBP' in text:
        currency = "GBP"

    # Strategy A: Ranges (80-100k)
    matches_k_range = re.search(r'(\d+)\s*[-–to]\s*(\d+)\s*[kK]', text)
    clean_numbers = []

    if matches_k_range:
        n1 = int(matches_k_range.group(1))
        n2 = int(matches_k_range.group(2))
        clean_numbers = [n1 * 1000, n2 * 1000]
    else:
        # Strategy B: Individual numbers (60k, 60,000)
        matches = re.findall(r'(\d+[,\.]?\d*)\s*([kK])?', text)
        for num_str, suffix in matches:
            clean_str = num_str.replace(',', '').replace('.', '')
            if not clean_str.isdigit(): continue
            val = float(clean_str)
            if suffix and suffix.lower() == 'k': val *= 1000
            if 15000 < val < 500000:  # Sanity check
                clean_numbers.append(int(val))

    if not clean_numbers:
        return None, None, None

    salary_min = min(clean_numbers)
    salary_max = max(clean_numbers) if len(clean_numbers) > 1 else salary_min

    return salary_min, salary_max, currency