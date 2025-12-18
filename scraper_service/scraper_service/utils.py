import re


def parse_salary(text):
    if not text:
        return None, None, None

    # 1. Identify Currency
    currency = "USD"  # Default
    if '€' in text or 'EUR' in text:
        currency = "EUR"
    elif '£' in text or 'GBP' in text:
        currency = "GBP"

    # 2. Extract Numbers using Regex
    # Looks for patterns like "60k", "60,000", "60.000"
    matches = re.findall(r'(\d+[,\.]?\d*)\s*([kK])?', text)

    clean_numbers = []
    for num_str, suffix in matches:
        # Remove commas/dots to get raw integer
        clean_num = float(num_str.replace(',', '').replace('.', ''))

        # Handle 'k' (e.g., 60k -> 60000)
        if suffix and suffix.lower() == 'k':
            clean_num *= 1000

        # Filter out tiny numbers (years, ids) and huge fake numbers
        if 10000 < clean_num < 500000:
            clean_numbers.append(int(clean_num))

    # 3. Determine Min/Max
    if not clean_numbers:
        return None, None, None

    salary_min = min(clean_numbers)
    # If there is only one number (e.g. "100k"), max is the same as min
    salary_max = max(clean_numbers) if len(clean_numbers) > 1 else salary_min

    return salary_min, salary_max, currency