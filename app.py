from pathlib import Path
import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime


st.set_page_config(page_title="Opp Win Probability", layout="centered")

# ----------------------
# Lightweight "data store"
# ----------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DM_CSV = DATA_DIR / "decision_makers.csv"
DIV_CSV = DATA_DIR / "divisions.csv"

# Default seeds if files don't exist
if not DM_CSV.exists():
    pd.DataFrame({"name":[
        "Adam Smith","Jane Doe","Maria Garcia","Chris Johnson","Priya Patel",
        "Liam Nguyen","Olivia Brown","Ethan Davis","Sophia Wilson","Noah Martinez"
    ]}).to_csv(DM_CSV, index=False)

if not DIV_CSV.exists():
    pd.DataFrame({"name":[
        "General Contracting", "Construction Services", "Coatings", "Landscaping"
    ]}).to_csv(DIV_CSV, index=False)

def load_picklist(path: Path, col="name") -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        if col not in df.columns:
            df = df.rename(columns={df.columns[0]: col})
        df[col] = df[col].astype(str).str.strip()
        df = df[df[col] != ""]
        df.drop_duplicates(subset=[col], inplace=True)
        df.sort_values(by=col, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df[[col]]
    except Exception:
        return pd.DataFrame({col: []})

def save_picklist(path: Path, df: pd.DataFrame, col="name"):
    df = df[[col]].copy()
    df[col] = df[col].astype(str).str.strip()
    df = df[df[col] != ""]
    df.drop_duplicates(subset=[col], inplace=True)
    df.to_csv(path, index=False)

# Load picklists
dm_df = load_picklist(DM_CSV, "name")
div_df = load_picklist(DIV_CSV, "name")

# ----------------------
# Global Config
# ----------------------
PROP_SENT_BASE_WIN_RATE   = 0.30
PROP_VERBAL_BASE_WIN_RATE = 0.75
WIN_PROB_MIN = 0.0
WIN_PROB_MAX = 1.0
AVG_PROP_TURNAROUND_DAYS = 14

STAGES = {
    "Proposal Sent": "PROPOSAL_SENT",
    "Verbal Approval": "VERBAL_APPROVAL"
}

st.title("Opportunity Win Probability Calculator")
st.caption("Self-contained app (Python + Streamlit). No database needed.")

# Sidebar: Data management
st.sidebar.header("Data")
with st.sidebar.expander("Decision Makers", expanded=False):
    st.write("Currently loaded:", len(dm_df), "names")
    st.dataframe(dm_df, use_container_width=True, hide_index=True)
    new_dm = st.text_input("Add a decision maker")
    if st.button("Add name", type="secondary"):
        if new_dm.strip():
            dm_df = pd.concat([dm_df, pd.DataFrame({"name":[new_dm.strip()]})], ignore_index=True)
            save_picklist(DM_CSV, dm_df, "name")
            st.success(f"Added: {new_dm.strip()}")
            st.rerun()
    dm_csv_file = st.file_uploader("Bulk import CSV (one column: name)", type=["csv"], key="dm_upl")
    if dm_csv_file is not None:
        try:
            tmp = pd.read_csv(dm_csv_file)
            if "name" not in tmp.columns:
                tmp = tmp.rename(columns={tmp.columns[0]: "name"})
            dm_df = pd.concat([dm_df, tmp[["name"]]], ignore_index=True)
            save_picklist(DM_CSV, dm_df, "name")
            st.success("Imported decision makers from CSV")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

with st.sidebar.expander("Divisions", expanded=False):
    st.write("Currently loaded:", len(div_df), "divisions")
    st.dataframe(div_df, use_container_width=True, hide_index=True)
    new_div = st.text_input("Add a division")
    if st.button("Add division", type="secondary"):
        if new_div.strip():
            div_df = pd.concat([div_df, pd.DataFrame({"name":[new_div.strip()]})], ignore_index=True)
            save_picklist(DIV_CSV, div_df, "name")
            st.success(f"Added: {new_div.strip()}")
            st.rerun()

# ----------------------
# Main form
# ----------------------
with st.form("calc_form", clear_on_submit=False):
    colA, colB = st.columns(2)
    decision_maker = colA.selectbox("Decision Maker", dm_df["name"].tolist(), index=0 if len(dm_df) else None)
    division = colB.selectbox("Division", div_df["name"].tolist(), index=0 if len(div_df) else None)

    stage_label = st.radio("Opportunity Stage", list(STAGES.keys()), horizontal=True)
    stage_code = STAGES[stage_label]

    est_rev = st.number_input("Estimated Revenue ($)", min_value=0.0, step=1000.0, format="%.2f")
    gp_pct  = st.number_input("Gross Profit %", min_value=0.0, max_value=1.0, step=0.01, value=0.20, help="Enter as a decimal (e.g., 0.22 for 22%)")
    win_prob = st.slider("Confidence (Win Probability)", min_value=0.0, max_value=1.0, value=0.50, step=0.01)

    submitted = st.form_submit_button("Calculate")

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def calc_probability_of_award(stage_code: str, win_prob: float) -> float:
    # normalize
    norm = (win_prob - WIN_PROB_MIN) / (WIN_PROB_MAX - WIN_PROB_MIN)
    base = PROP_SENT_BASE_WIN_RATE
    delta = (PROP_VERBAL_BASE_WIN_RATE - PROP_SENT_BASE_WIN_RATE) if stage_code == "VERBAL_APPROVAL" else 0.0
    return clamp01(base + delta * norm)

if 'history' not in st.session_state:
    st.session_state['history'] = []

if submitted:
    poa = calc_probability_of_award(stage_code, win_prob)
    expected_value = est_rev * poa
    expected_gp = expected_value * gp_pct

    st.success("Calculation complete")
    st.metric("Probability of Award", f"{poa:.2%}")
    st.metric("Expected Value", f"${expected_value:,.2f}")
    st.metric("Expected Gross Profit", f"${expected_gp:,.2f}")

    with st.expander("Breakdown", expanded=True):
        st.write(f"Base (Proposal Sent): **{PROP_SENT_BASE_WIN_RATE:.2f}**")
        st.write(f"Delta to Verbal: **{(PROP_VERBAL_BASE_WIN_RATE - PROP_SENT_BASE_WIN_RATE):.2f}**")
        st.write(f"Stage: **{stage_label}** → delta applied: **{ 'Yes' if stage_code=='VERBAL_APPROVAL' else 'No' }**")
        st.write(f"Normalized confidence: **{win_prob:.2f}**")
        st.code("probability_of_award = base + delta * norm", language="text")

    # append to local "history"
    st.session_state['history'].append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "decision_maker": decision_maker,
        "division": division,
        "stage": stage_label,
        "estimated_revenue": est_rev,
        "gross_profit_pct": gp_pct,
        "win_probability": win_prob,
        "probability_of_award": poa,
        "expected_value": expected_value,
        "expected_gross_profit": expected_gp
    })

# Show simple history (does not persist across app restarts)
if st.session_state['history']:
    st.subheader("Recent Calculations (session)")
    hist_df = pd.DataFrame(st.session_state['history'])
    st.dataframe(hist_df, use_container_width=True, hide_index=True)
    st.download_button("Download Results (CSV)", hist_df.to_csv(index=False), file_name="opp_calc_results.csv", mime="text/csv")

st.caption("Config: Proposal Sent base 0.30, Verbal base 0.75, turnaround 14 days. You can edit data files in ./data/*.csv.")
