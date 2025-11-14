from backend.nlp.pipeline import extract_structure

def test_login_extraction():
    text = "User should be able to login with valid credentials."
    s = extract_structure(text)
    assert "steps" in s and len(s["steps"]) >= 3
    actions = [st["action"] for st in s["steps"]]
    assert "input" in actions and "click" in actions
