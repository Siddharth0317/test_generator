"""
Optimized spaCy-based rule extractor with simple fallback heuristics.
Keep patterns small and extend in future.
"""
from typing import Dict, Any, List
import spacy
from spacy.matcher import Matcher
import logging

logger = logging.getLogger(__name__)

# Load once
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    # helpful error message if user forgot to download model
    raise RuntimeError("spaCy model not found. Run: python -m spacy download en_core_web_sm") from e

matcher = Matcher(nlp.vocab)

# Define patterns (extend these for other actions)
matcher.add("LOGIN", [[{"LEMMA": "login"}]])
matcher.add("REGISTER", [[{"LEMMA": "register"}]])
matcher.add("SEARCH", [[{"LEMMA": "search"}]])
matcher.add("ADD_TO_CART", [[{"LEMMA": "add"}, {"LOWER":"to", "OP":"?"}, {"LOWER":"cart", "OP":"?"}] ])

def _map_login_steps() -> List[Dict[str, Any]]:
    return [
        {"action": "open", "target": "login_page"},
        {"action": "input", "target": "username_field", "value": "<valid_username>"},
        {"action": "input", "target": "password_field", "value": "<valid_password>"},
        {"action": "click", "target": "login_button"},
        {"action": "assert", "target": "dashboard", "expected": "visible"},
    ]

def _map_register_steps() -> List[Dict[str, Any]]:
    return [
        {"action": "open", "target": "registration_page"},
        {"action": "input", "target": "name_field", "value": "<name>"},
        {"action": "input", "target": "email_field", "value": "<email>"},
        {"action": "click", "target": "register_button"},
        {"action": "assert", "target": "confirmation", "expected": "visible"},
    ]

def _map_search_steps() -> List[Dict[str, Any]]:
    return [
        {"action": "open", "target": "home_page"},
        {"action": "input", "target": "search_box", "value": "<query>"},
        {"action": "click", "target": "search_button"},
        {"action": "assert", "target": "results", "expected": "contain <query>"},
    ]

def _map_add_to_cart_steps() -> List[Dict[str, Any]]:
    return [
        {"action": "open", "target": "product_page"},
        {"action": "click", "target": "add_to_cart_button"},
        {"action": "assert", "target": "cart", "expected": "contains product"},
    ]

def extract_structure(text: str) -> Dict[str, Any]:
    """
    Return basic structure: { title: str, steps: [ { step, action, ... } ] }
    """
    doc = nlp(text)
    matches = matcher(doc)
    lowered = text.lower()
    steps = []

    # Prioritize direct pattern matches
    labels = {nlp.vocab.strings[match_id] for match_id, start, end in matches}
    if "LOGIN" in labels or "login" in lowered:
        steps = _map_login_steps()
    elif "REGISTER" in labels or "register" in lowered:
        steps = _map_register_steps()
    elif "SEARCH" in labels or "search" in lowered:
        steps = _map_search_steps()
    elif "ADD_TO_CART" in labels or "add to cart" in lowered or ("add" in lowered and "cart" in lowered):
        steps = _map_add_to_cart_steps()
    else:
        # Fallback: analyze sentences, look for verbs and produce generic steps
        step_no = 1
        for sent in doc.sents:
            verbs = [tok.lemma_.lower() for tok in sent if tok.pos_ == "VERB"]
            if not verbs:
                continue
            if "open" in verbs or "navigate" in verbs:
                steps.append({"action": "open", "target": "unknown", "note": sent.text})
            elif any(v in verbs for v in ("click", "press", "select")):
                steps.append({"action": "click", "target": "unknown", "note": sent.text})
            elif any(v in verbs for v in ("enter", "type", "input")):
                steps.append({"action": "input", "target": "unknown", "value": "<value>", "note": sent.text})
            elif "assert" in verbs or "see" in verbs or "display" in verbs:
                steps.append({"action": "assert", "target": "unknown", "expected": sent.text})
            step_no += 1

    # Number steps
    for i, s in enumerate(steps, start=1):
        s["step"] = i

    title = text.strip()[:120]
    return {"title": title, "steps": steps}
