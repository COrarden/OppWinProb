# frontend/app.py — fixed to work without secrets.toml and be more robust

import os
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="OppWinProb CRUD + Calculator", layout="wide")

# ---- Safe API base resolution (no secrets file required) ----
try:
    API_BASE = st.secrets["API_BASE"]  # if a secrets.toml exists, use it
except Exception:
    API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")  # fallback

# Optional: allow quick override from the UI (handy if backend runs on a different port)
with st.sidebar:
    st.caption("Backend API base")
    API_BASE = st.text_input("API_BASE", value=API_BASE, help="e.g. http://127.0.0.1:8000")

# ---- HTTP helpers with timeouts & graceful failures ----
DEFAULT_TIMEOUT = 10

def _get(url, **kwargs):
    try:
        return requests.get(url, timeout=DEFAULT_TIMEOUT, **kwargs)
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return None

def _post(url, **kwargs):
    try:
        return requests.post(url, timeout=DEFAULT_TIMEOUT, **kwargs)
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return None

def _put(url, **kwargs):
    try:
        return requests.put(url, timeout=DEFAULT_TIMEOUT, **kwargs)
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return None

def _delete(url, **kwargs):
    try:
        return requests.delete(url, timeout=DEFAULT_TIMEOUT, **kwargs)
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return None

# ---- Export helpers ----
def get_calcs_count():
    r = _get(f"{API_BASE}/calculations/count")
    if r and r.ok:
        return r.json().get("count", 0)
    return 0

def fetch_csv(endpoint, params):
    r = _get(f"{API_BASE}{endpoint}", params=params)
    if r and r.ok:
        return r.content
    return b""

# ---- API wrappers ----
def login(username, password):
    r = _post(f"{API_BASE}/auth/login", json={"username": username, "password": password})
    if r and r.ok:
        data = r.json()
        return data.get("ok", False), data.get("message", "")
    return False, "Error contacting server"

def list_divisions():
    r = _get(f"{API_BASE}/divisions")
    return r.json() if r and r.ok else []

def create_division(name, weight_modifier):
    r = _post(f"{API_BASE}/divisions", json={"name": name, "weight_modifier": weight_modifier})
    return r.json() if r and r.ok else {"detail": "Request failed"}

def update_division(div_id, name, weight_modifier):
    r = _put(f"{API_BASE}/divisions/{div_id}", json={"name": name, "weight_modifier": weight_modifier})
    return r.json() if r and r.ok else {"detail": "Request failed"}

def delete_division(div_id):
    r = _delete(f"{API_BASE}/divisions/{div_id}")
    return r.json() if r and r.ok else {"ok": False, "detail": "Request failed"}

def list_dms():
    r = _get(f"{API_BASE}/decision_makers")
    return r.json() if r and r.ok else []

def create_dm(name, role, score):
    r = _post(f"{API_BASE}/decision_makers", json={"name": name, "role": role, "score": score})
    return r.json() if r and r.ok else {"detail": "Request failed"}

def update_dm(dm_id, name, role, score):
    r = _put(f"{API_BASE}/decision_makers/{dm_id}", json={"name": name, "role": role, "score": score})
    return r.json() if r and r.ok else {"detail": "Request failed"}

def delete_dm(dm_id):
    r = _delete(f"{API_BASE}/decision_makers/{dm_id}")
    return r.json() if r and r.ok else {"ok": False, "detail": "Request failed"}

def create_calc(division_id, dm_id, budget_fit, timeline_fit, result):
    payload = {
        "division_id": division_id,
        "decision_maker_id": dm_id,
        "budget_fit": budget_fit,
        "timeline_fit": timeline_fit,
        "result": result
    }
    r = _post(f"{API_BASE}/calculations", json=payload)
    return r.json() if r and r.ok else {"detail": "Request failed"}

def list_calcs():
    r = _get(f"{API_BASE}/calculations")
    return r.json() if r and r.ok else []

# ---- UI state & title ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.title("OppWinProb: CRUD + Calculator (SQLite)")

# ---- Auth ----
if not st.session_state.logged_in:
    st.subheader("Login")
    with st.form("login"):
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="admin123")
        submitted = st.form_submit_button("Log in")
        if submitted:
            ok, msg = login(u, p)
            if ok:
                st.session_state.logged_in = True
                st.success("Logged in")
                st.experimental_rerun()
            else:
                st.error(msg)
else:
    tabs = st.tabs(["Divisions", "Decision Makers", "Calculator", "History", "Export"])

    # ---- Divisions ----
    with tabs[0]:
        st.header("Divisions")
        cols = st.columns(2)
        with cols[0]:
            st.subheader("Create")
            with st.form("create_div"):
                name = st.text_input("Division Name")
                wm = st.number_input("Weight Modifier (±)", value=0.0, step=0.01, format="%.2f")
                if st.form_submit_button("Create"):
                    if name.strip():
                        resp = create_division(name.strip(), wm)
                        if "id" in resp:
                            st.success(f"Created: {resp['name']} (id={resp['id']})")
                        else:
                            st.error(resp.get("detail", resp))
                    else:
                        st.warning("Name required")
        with cols[1]:
            st.subheader("Existing")
            divs = list_divisions()
            if isinstance(divs, list) and divs:
                df = pd.DataFrame(divs)
                st.dataframe(df)
                st.markdown("---")
                st.caption("Edit / Delete")
                sel = st.selectbox("Select Division", options=divs, format_func=lambda d: f"{d['id']}: {d['name']}")
                if sel:
                    new_name = st.text_input("Name", value=sel["name"])
                    new_wm = st.number_input("Weight Modifier", value=float(sel["weight_modifier"]), step=0.01, format="%.2f")
                    c1, c2 = st.columns(2)
                    if c1.button("Save Update"):
                        resp = update_division(sel["id"], new_name, new_wm)
                        if "id" in resp:
                            st.success("Updated")
                            st.experimental_rerun()
                        else:
                            st.error(resp.get("detail", resp))
                    if c2.button("Delete"):
                        resp = delete_division(sel["id"])
                        if resp.get("ok"):
                            st.success("Deleted")
                            st.experimental_rerun()
                        else:
                            st.error(resp)

    # ---- Decision Makers ----
    with tabs[1]:
        st.header("Decision Makers")
        cols = st.columns(2)
        with cols[0]:
            st.subheader("Create")
            with st.form("create_dm_form"):
                name = st.text_input("Name")
                role = st.text_input("Role", value="Manager")
                score = st.slider("Score (0-100)", min_value=0, max_value=100, value=60)
                if st.form_submit_button("Create"):
                    if name.strip():
                        resp = create_dm(name.strip(), role.strip(), score)
                        if "id" in resp:
                            st.success(f"Created: {resp['name']} (id={resp['id']})")
                        else:
                            st.error(resp.get("detail", resp))
                    else:
                        st.warning("Name required")
        with cols[1]:
            st.subheader("Existing")
            dms = list_dms()
            if isinstance(dms, list) and dms:
                df = pd.DataFrame(dms)
                st.dataframe(df)
                st.markdown("---")
                st.caption("Edit / Delete")
                sel = st.selectbox("Select Decision Maker", options=dms, format_func=lambda d: f"{d['id']}: {d['name']} ({d['role']})")
                if sel:
                    new_name = st.text_input("Name ", value=sel["name"], key="dm_edit_name")
                    new_role = st.text_input("Role ", value=sel["role"], key="dm_edit_role")
                    new_score = st.slider("Score", min_value=0, max_value=100, value=int(sel["score"]), key="dm_edit_score")
                    c1, c2 = st.columns(2)
                    if c1.button("Save Update", key="dm_save"):
                        resp = update_dm(sel["id"], new_name, new_role, new_score)
                        if "id" in resp:
                            st.success("Updated")
                            st.experimental_rerun()
                        else:
                            st.error(resp.get("detail", resp))
                    if c2.button("Delete", key="dm_del"):
                        resp = delete_dm(sel["id"])
                        if resp.get("ok"):
                            st.success("Deleted")
                            st.experimental_rerun()
                        else:
                            st.error(resp)

    # ---- Calculator ----
    with tabs[2]:
        st.header("Win Probability Calculator")
        divs = list_divisions()
        dms = list_dms()

        if not divs or not dms:
            st.info("Please create at least one Division and one Decision Maker first.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                div_sel = st.selectbox("Division", options=divs, format_func=lambda d: f"{d['name']} (wm={d['weight_modifier']:+.2f})")
            with c2:
                dm_sel = st.selectbox("Decision Maker", options=dms, format_func=lambda d: f"{d['name']} (score={d['score']})")
            with c3:
                st.caption("Context Weights")
                budget_fit = st.slider("Budget Fit (0-1)", min_value=0.0, max_value=1.0, value=0.6, step=0.05)
                timeline_fit = st.slider("Timeline Fit (0-1)", min_value=0.0, max_value=1.0, value=0.6, step=0.05)

            def preview_prob(dm_score, wm, bf, tf):
                base = 0.25
                dm_comp = (dm_score/100.0)*0.5
                fit_comp = ((bf+tf)/2.0)*0.2
                prob = base + dm_comp + wm + fit_comp
                prob = max(0.0, min(1.0, prob))
                return prob

            result = preview_prob(dm_sel["score"], div_sel["weight_modifier"], budget_fit, timeline_fit)
            st.metric("Win Probability", f"{result*100:.1f}%")

            if st.button("Save Result"):
                resp = create_calc(div_sel["id"], dm_sel["id"], budget_fit, timeline_fit, result)
                if "id" in resp:
                    st.success(f"Saved calculation #{resp['id']}")
                else:
                    st.error(resp)

    # ---- History ----
    with tabs[3]:
        st.header("History")
        calcs = list_calcs()
        if isinstance(calcs, list) and calcs:
            df = pd.DataFrame(calcs)
            st.dataframe(df)
        else:
            st.info("No calculations yet.")

    # ---- Export (batched) ----
    with tabs[4]:
        st.header("Export (Batched)")
        st.write("Download large datasets in smaller chunks to avoid overloading memory.")

        col1, col2 = st.columns(2)
        batch_size = col1.number_input("Batch size (rows per file)", min_value=100, max_value=100_000, value=1000, step=100)
        total = get_calcs_count()
        col2.metric("Total calculation rows", total)

        if total == 0:
            st.info("No calculation rows to export yet.")
        else:
            total_pages = (total + batch_size - 1) // batch_size
            st.write(f"Pages: {total_pages} (0-based)")

            page = st.number_input("Page to prepare", min_value=0, max_value=max(total_pages-1, 0), value=0, step=1)
            offset = int(page * batch_size)
            st.caption(f"Chunk rows {offset} to {min(offset+batch_size-1, total-1)}")
            if st.button("Generate download for this page"):
                data = fetch_csv("/calculations/export", {"offset": offset, "limit": int(batch_size)})
                if data:
                    st.download_button(
                        label=f"Download calculations_{offset}_{min(offset+batch_size-1, total-1)}.csv",
                        data=data,
                        file_name=f"calculations_{offset}_{min(offset+batch_size-1, total-1)}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Failed to fetch CSV. Is the backend running?")

            st.divider()
            st.subheader("Other tables (Divisions / Decision Makers)")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Download Divisions CSV"):
                    data = fetch_csv("/divisions/export", {"offset": 0, "limit": 100000})
                    if data:
                        st.download_button(
                            label="Download divisions.csv",
                            data=data,
                            file_name="divisions.csv",
                            mime="text/csv"
                        )
                    else:
                        st.error("Failed to fetch Divisions CSV.")
            with c2:
                if st.button("Download Decision Makers CSV"):
                    data = fetch_csv("/decision_makers/export", {"offset": 0, "limit": 100000})
                    if data:
                        st.download_button(
                            label="Download decision_makers.csv",
                            data=data,
                            file_name="decision_makers.csv",
                            mime="text/csv"
                        )
                    else:
                        st.error("Failed to fetch Decision Makers CSV.")
