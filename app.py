import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from agent import career_agent

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Career Intelligence Agent", layout="wide")

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("""
<h1 style='text-align:center'>Career & Skills Intelligence Platform</h1>
<h4 style='text-align:center;color:gray'>
Enterprise Career Agent • HR & Manager Decisions
</h4>
""", unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# SIDEBAR CONFIG
# --------------------------------------------------
st.sidebar.header("Analysis Configuration")

analysis_mode = st.sidebar.radio(
    "Analysis Mode",
    ["Employee Record Analysis", "Scenario / What-if Analysis"]
)

view_mode = st.sidebar.selectbox("View Mode", ["Manager", "HR"])

# --------------------------------------------------
# DATA SOURCE LOGIC (STRICT SEPARATION)
# --------------------------------------------------
emp = {}

if analysis_mode == "Employee Record Analysis":
    uploaded_file = st.sidebar.file_uploader("Upload Employee CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        selected_emp_id = st.sidebar.selectbox(
            "Select Employee ID",
            df["employee_id"].astype(str).unique()
        )
        emp = df[df["employee_id"].astype(str) == selected_emp_id].iloc[0]

# --------------------------------------------------
# INPUT DATA (CONDITIONAL VISIBILITY)
# --------------------------------------------------
if analysis_mode == "Employee Record Analysis":
    # READ-ONLY SNAPSHOT
    employee_id = emp.get("employee_id", "")
    name = emp.get("name", "")
    role = emp.get("role", "")
    target_role = emp.get("target_role", "")
    experience = int(emp.get("experience", 0))
    skills = emp.get("skills", "")
    certifications = emp.get("certifications", "")

else:
    # SCENARIO INPUT (EDITABLE)
    st.sidebar.subheader("Scenario Inputs")
    employee_id = st.sidebar.text_input("Employee ID (optional)")
    name = st.sidebar.text_input("Employee Name")
    role = st.sidebar.text_input("Current Role")
    target_role = st.sidebar.text_input("Target Role")
    experience = st.sidebar.number_input("Experience (years)", 0, 40)
    skills = st.sidebar.text_area("Skills (comma separated)")
    certifications = st.sidebar.text_area("Certifications (if any)")

# --------------------------------------------------
# SELF-ASSESSMENT (BOTH MODES)
# --------------------------------------------------
st.sidebar.subheader("Self-Assessment")

self_confidence = st.sidebar.selectbox(
    "Overall Skill Confidence",
    ["Foundational", "Working Professional", "Advanced", "Expert"]
)

ownership_level = st.sidebar.selectbox(
    "Primary Responsibility Level",
    [
        "Execution-focused",
        "Independent contributor",
        "Module owner",
        "End-to-end owner"
    ]
)

# --------------------------------------------------
# HR APPROVAL
# --------------------------------------------------
approval_status = "Draft"
if view_mode == "HR":
    approval_status = st.sidebar.selectbox(
        "Approval Status",
        ["Draft", "Approved", "Rejected"]
    )

# --------------------------------------------------
# MAIN UI PANELS
# --------------------------------------------------
left, right = st.columns([1.3, 2.7])

with left:
    if analysis_mode == "Employee Record Analysis":
        st.subheader("👤 Employee Snapshot (Read-only)")
        st.text_input("Employee ID", employee_id, disabled=True)
        st.text_input("Name", name, disabled=True)
        st.text_input("Current Role", role, disabled=True)
        st.text_input("Target Role", target_role, disabled=True)
        st.text_input("Experience", f"{experience} years", disabled=True)

    else:
        st.subheader("✏️ Scenario Inputs")
        st.info("Simulated inputs for career planning")

with right:
    st.subheader("🧠 Career Intelligence Output")
    output_container = st.container()

    if st.button("Run Career Analysis"):
        with st.spinner("Generating insights..."):
            prompt = f"""
You are a Senior Enterprise HR Career Intelligence Agent.

Employee ID: {employee_id}
Name: {name}
Current Role: {role}
Target Role: {target_role}
Experience: {experience} years
Skills: {skills}
Certifications: {certifications}

Self-Assessment:
Confidence: {self_confidence}
Responsibility: {ownership_level}

Rules:
- No numeric skill ratings
- Executive HR-safe language
- Strategic promotion framing

Deliver:
Executive overview, skill assessment,
career path, readiness statement,
roadmap, HR notes.
"""
            insights = career_agent(prompt)
            st.session_state["insights"] = insights
            output_container.markdown(insights)
    else:
        st.info("Run analysis to view results")

# --------------------------------------------------
# PDF DOWNLOAD
# --------------------------------------------------
if approval_status == "Approved" and "insights" in st.session_state:
    if st.button("Download Career Report (PDF)"):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(tmp.name, pagesize=A4)
        styles = getSampleStyleSheet()
        doc.build([Paragraph(st.session_state["insights"], styles["Normal"])])

        with open(tmp.name, "rb") as f:
            st.download_button(
                "Download PDF",
                f,
                file_name=f"{employee_id}_Career_Report.pdf",
                mime="application/pdf"
            )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.info("Enterprise Career Intelligence Agent • Compunnel")
