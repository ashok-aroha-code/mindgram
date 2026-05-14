import re
from bs4 import BeautifulSoup

def extract_ce_credits(text):
    """
    Extracts CE/CECH credit numbers from a string.
    Example: 'Wound Care Update (1.5 CE)' -> '1.5'
    """
    if not text:
        return ""
    match = re.search(r"(\d+\.?\d*)\s*(?:CE|CECH)", text, re.IGNORECASE)
    return match.group(1) if match else ""

def clean_html_text(html_content, separator="\n"):
    """
    Converts HTML to clean, readable text using BeautifulSoup.
    """
    if not html_content:
        return "-"
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator=separator).strip()

def normalize_authors(authors_list, exclude_keywords=None):
    """
    Cleans up a list of author names, removing degrees and excluded keywords.
    """
    if not authors_list:
        return ""
    
    exclude_keywords = exclude_keywords or ["Room", "Faculty"]
    cleaned = []
    for name in authors_list:
        if not name: continue
        # Skip if any exclude keyword is in the name
        if any(kw in name for kw in exclude_keywords):
            continue
        # Optional: Strip common degrees (MD, PhD, etc.) if requested later
        cleaned.append(name.strip())
    
    return "; ".join(cleaned)

def smart_split_html(html_content, split_tag="b", number_pattern=r"^[A-Z0-9\.]+"):
    """
    Splits a single HTML block into multiple sub-sections (abstracts).
    Commonly used for 'Oral Abstract' sessions where many abstracts are in one field.
    """
    if not html_content:
        return []
        
    # First try splitting by the tag (usually <b>)
    blocks = re.split(rf"(?=<{split_tag}>)", html_content)
    
    # If we only have one block, try splitting by double <br>
    if len(blocks) <= 1:
        # Normalize BR tags and split by double BR
        normalized_html = re.sub(r'<br\s*/?>', '<br>', html_content, flags=re.IGNORECASE)
        blocks = re.split(r'<br>\s*<br>', normalized_html)

    results = []
    
    for block in blocks:
        if not block.strip() or len(clean_html_text(block)) < 10:
            continue
            
        soup = BeautifulSoup(block, 'html.parser')
        header_tag = soup.find(split_tag)
        
        full_title = ""
        number = ""
        
        if header_tag:
            full_title = header_tag.text.strip()
        else:
            # Fallback: Use the first line of text as the title
            text_lines = [line.strip() for line in clean_html_text(block).split("\n") if line.strip()]
            if text_lines:
                full_title = text_lines[0]
                
        # Extract number if it matches the pattern (e.g., 'K2.01')
        if full_title:
            num_match = re.match(number_pattern, full_title)
            if num_match:
                number = num_match.group(0)
                full_title = full_title.replace(number, "").strip().strip(":").strip()
            
        results.append({
            "title": full_title,
            "number": number,
            "html": block,
            "text": clean_html_text(block)
        })
        
    return results
