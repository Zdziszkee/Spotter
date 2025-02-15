from typing import List
import re

STREET_REGEXES = [
    re.compile(r'\bul(?!ica|icy)\.?\s*([^\d]+?)(?=\s+\d|\b)'),  # Merged Cases 1, 2, 3: Matches "ul" with an optional dot and whitespace, but excludes "ulica" and "ulicy"; stops before house numbers
    re.compile(r'ulicy (.+)'),                   # Case 4: "ulicy [streetname]"
    re.compile(r'ulica (.+)'),                   # Case 5: "ulica [streetname]"
    re.compile(r'al\.(\S.*)'),                    # Case 7: "al.[streetname]" (no space after '.')
    re.compile(r'al\. (.+)'),                     # Case 8: "al. [streetname]" (with space after '.')
    re.compile(r'alei (.+)'),                     # Case 9: "alei [streetname]"
    re.compile(r'aleja (.+)'),                    # Case 10: "aleja [streetname]"
    re.compile(r'\bul(?!ica|icy)\.?\s*(\S+\s+\S+)'),  # Duplicate for two-word street names: e.g., ul. Stefana Batorego
    re.compile(r'ulicy (\S+\s+\S+)'),                  # Duplicate for two-word street names
    re.compile(r'ulica (\S+\s+\S+)'),                  # Duplicate for two-word street names
    re.compile(r'al\.(\S+\s+\S+)'),                   # Duplicate for two-word street names (no space after '.')
    re.compile(r'al\. (\S+\s+\S+)'),                   # Duplicate for two-word street names (with space after '.')
    re.compile(r'alei (\S+\s+\S+)'),                   # Duplicate for two-word street names
    re.compile(r'aleja (\S+\s+\S+)')                   # Duplicate for two-word street names
]

def extract_street(full_text: str, streetnames: List[str]) -> str:
    """
    Extracts a street name from the given text by applying multiple regexes and
    comparing the results with a list of known street names.

    :param full_text: The full text (e.g., title plus description) to search for a street.
    :param streetnames: The list of known street names.
    :return: The matching street name if found, or an empty string.
    """
    street = ""
    candidate = ""
    for regex in STREET_REGEXES:
        match = regex.search(full_text)
        if match:
            candidate = match.group(1).strip()
            # Replace abbreviation "św" with "świętego" if it appears as a separate word.
            candidate = re.sub(r'\bśw\b', 'świętego', candidate)

            # Apply hardcoded rules to modify candidate if required.
            if candidate.lower().endswith("iego"):
                candidate = candidate[:-4] + "a"
            elif candidate.lower().endswith("iej"):
                candidate = candidate[:-3] + "a"
            elif candidate.lower().endswith("ej"):
                candidate = candidate[:-2] + "a"

            # Compare candidate (ignoring case) against the stored street names.
            for streetname in streetnames:
                if candidate.lower() == streetname.lower():
                    street = streetname
                    break
            if street:
                break

    # Fallback: if no candidate was validated via regex,
    # search for any known street name in the full text.
    if not street:
        for streetname in streetnames:
            pattern = re.compile(r'\b' + re.escape(streetname) + r'\b', re.IGNORECASE)
            if pattern.search(full_text):
                street = streetname
                break
    return street
