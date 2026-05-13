from .files import load_json, save_json, ensure_dir
from .browser import (
    setup_driver_options,
    safe_click,
    scroll_to_element,
    scroll_down_to_bottom,
    dismiss_cookie_banner,
    wait_for_element,
    get_text_safely
)
from .human import HumanBehaviors
from .timer import ScraperTimer
from .text import (
    extract_ce_credits,
    clean_html_text,
    normalize_authors,
    smart_split_html
)

__all__ = [
    "load_json",
    "save_json",
    "ensure_dir",
    "setup_driver_options",
    "safe_click",
    "scroll_to_element",
    "scroll_down_to_bottom",
    "dismiss_cookie_banner",
    "HumanBehaviors",
    "ScraperTimer",
    "wait_for_element",
    "get_text_safely",
    "extract_ce_credits",
    "clean_html_text",
    "normalize_authors",
    "smart_split_html"
]