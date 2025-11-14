# frontend/app.py
import streamlit as st
import requests
import json
import pandas as pd
import time
from typing import List, Dict

API_URL = "http://127.0.0.1:8000"  # ensure backend running

st.set_page_config(
    page_title="Testcase Generator",
    page_icon="🧪",
    layout="wide",
)

# ---------- UI: Header ----------
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px">
      <div style="font-size:42px">🧪</div>
      <div>
        <h1 style="margin:0 0 4px 0">Testcase Generator</h1>
        <div style="color:gray;margin-top:0">Convert plain-English requirements into structured test cases — JSON / CSV / PDF. Demo includes an optional Selenium dry-run.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("---")

# ---------- Sidebar (controls & examples) ----------
with st.sidebar:
    st.header("Settings")
    template_style = st.selectbox("Template style", ["Numbered Steps", "Given/When/Then"])
    selenium_headless = st.checkbox("Run Selenium in headless mode", value=True)
    use_server_export = st.checkbox("Use server-side exports (CSV/PDF)", value=True)
    st.markdown("---")
    st.write("Example requirements")
    examples = {
        "Login (valid creds)": "User should be able to login with valid credentials.",
        "Registration (name + email)": "The user can register by entering name and email and clicking register.",
        "Search products": "Search for products using the search bar and see results containing the query."
    }
    example_key = st.selectbox("Choose example (click to populate)", [""] + list(examples.keys()))
    if example_key:
        st.session_state.setdefault("last_input", examples[example_key])
    st.markdown("---")
    st.write("Tips")
    st.info("Write requirements in simple sentences. Try to include action verbs like 'login', 'search', 'register' for best results.")

# ---------- Main: Input form ----------
with st.form("req_form", clear_on_submit=False):
    st.subheader("Enter requirement(s)")
    req_text = st.text_area(
        "Natural language requirement(s)",
        value=st.session_state.get("last_input", ""),
        height=180,
        placeholder="e.g., User should be able to login with valid credentials."
    )
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        generate_btn = st.form_submit_button("Generate ✨")
    with col2:
        csv_local_btn = st.form_submit_button("Generate CSV (local)")
    with col3:
        pdf_btn = st.form_submit_button("Export PDF (server)" if use_server_export else "Export PDF (not available)")
    st.markdown("")

# ---------- Helpers ----------
def call_generate_api(text: str):
    try:
        r = requests.post(API_URL + "/generate", json={"text": text}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error while generating: {e}")
        return None

def call_export_csv_server(text: str):
    try:
        r = requests.post(API_URL + "/export/csv", json={"text": text}, timeout=20)
        r.raise_for_status()
        return r.content
    except Exception as e:
        st.error(f"CSV export failed: {e}")
        return None

def call_export_pdf_server(text: str):
    try:
        r = requests.post(API_URL + "/export/pdf", json={"text": text}, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        st.error(f"PDF export failed: {e}")
        return None

def call_run_selenium(tc: Dict, headless: bool = True):
    try:
        payload = {"testcase": tc, "headless": headless}
        r = requests.post(API_URL + "/run-selenium", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Selenium call failed: {e}")
        return None

def tc_to_dataframe(tc: Dict) -> pd.DataFrame:
    rows = []
    for s in tc.get("steps", []):
        rows.append({
            "step": s.get("step"),
            "action": s.get("action"),
            "target": s.get("target") or "",
            "value": s.get("value") or "",
            "expected": s.get("expected") or "",
            "note": s.get("note") or ""
        })
    return pd.DataFrame(rows)

# ---------- Actions ----------
if generate_btn:
    if not req_text.strip():
        st.warning("Please enter requirement text before generating.")
    else:
        with st.spinner("Calling generate API..."):
            resp = call_generate_api(req_text)
        if resp:
            st.success("Generated successfully.")
            st.session_state["last_tcs"] = resp.get("testcases", [])
            st.session_state["last_req"] = req_text

if csv_local_btn:
    if not req_text.strip():
        st.warning("Enter requirement text to generate CSV locally.")
    else:
        # call server generate then convert locally
        resp = call_generate_api(req_text)
        if resp:
            tcs = resp.get("testcases", [])
            # flatten into DataFrame
            df_rows = []
            for tc in tcs:
                for s in tc.get("steps", []):
                    df_rows.append({"tc_id": tc.get("id"), "title": tc.get("title"),
                                    "step": s.get("step"), "action": s.get("action"),
                                    "target": s.get("target") or "", "value": s.get("value") or "",
                                    "expected": s.get("expected") or ""})
            df = pd.DataFrame(df_rows)
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv_bytes, file_name="testcases_local.csv", mime="text/csv")

if pdf_btn and use_server_export:
    if not req_text.strip():
        st.warning("Enter requirement text to export PDF.")
    else:
        with st.spinner("Requesting server-side PDF..."):
            pdf_bytes = call_export_pdf_server(req_text)
        if pdf_bytes:
            st.download_button("Download PDF", pdf_bytes, file_name="testcases.pdf", mime="application/pdf")

# ---------- Display results ----------
tcs: List[Dict] = st.session_state.get("last_tcs", [])

if not tcs:
    st.info("No testcases generated yet. Type a requirement and click **Generate**.")
else:
    st.write("### Generated testcases")
    main_col, sidebar_col = st.columns([3, 1])

    with sidebar_col:
        st.markdown("**Quick actions**")
        if st.button("Download all JSON"):
            all_json = json.dumps(tcs, indent=2)
            st.download_button("Download JSON (all)", all_json, file_name="all_testcases.json", mime="application/json")
        if st.button("Download CSV (all)"):
            # flatten
            rows = []
            for tc in tcs:
                for s in tc.get("steps", []):
                    rows.append({
                        "tc_id": tc.get("id"),
                        "title": tc.get("title"),
                        "step": s.get("step"),
                        "action": s.get("action"),
                        "target": s.get("target") or "",
                        "value": s.get("value") or "",
                        "expected": s.get("expected") or ""
                    })
            df_all = pd.DataFrame(rows)
            st.download_button("Download CSV (all)", df_all.to_csv(index=False).encode("utf-8"), file_name="testcases_all.csv", mime="text/csv")

    # iterate testcases
    for idx, tc in enumerate(tcs):
        with st.container():
            st.markdown(f"#### 🧾 {tc.get('id')} — {tc.get('title')}")
            cols = st.columns([3, 1])
            with cols[1]:
                if st.button(f"Run Selenium ▶ {tc.get('id')}", key=f"run_{tc.get('id')}"):
                    with st.spinner("Running Selenium (this may take a while)..."):
                        result = call_run_selenium(tc, headless=selenium_headless)
                        if result:
                            st.success("Selenium run finished")
                            st.json(result.get("results"))
            # show editable steps table
            df = tc_to_dataframe(tc)
            st.markdown("**Steps** — edit inline and download")
            edited = st.data_editor(df, num_rows="dynamic", key=f"editor_{tc.get('id')}")
            # Provide download buttons for edited version
            csv_bytes = edited.to_csv(index=False).encode("utf-8")
            st.download_button("Download Edited CSV", csv_bytes, file_name=f"{tc.get('id')}_edited.csv", mime="text/csv")
            st.markdown("**JSON output**")
            # Build JSON from edited
            reconstructed = {
                "id": tc.get("id"),
                "title": tc.get("title"),
                "steps": []
            }
            for _, row in edited.iterrows():
                reconstructed["steps"].append({
                    "step": int(row.get("step")) if not pd.isna(row.get("step")) else None,
                    "action": row.get("action"),
                    "target": row.get("target") if row.get("target") else None,
                    "value": row.get("value") if row.get("value") else None,
                    "expected": row.get("expected") if row.get("expected") else None
                })
            st.code(json.dumps(reconstructed, indent=2), language="json")
            # small spacing
            st.markdown("---")

# ---------- Footer ----------
st.markdown(
    """
    <div style="font-size:13px;color:gray">
      Built with ❤️ — backend: FastAPI • NLP: spaCy • UI: Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
