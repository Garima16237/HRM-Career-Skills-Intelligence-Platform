import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from agent import career_agent   # Groq API agent

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Career Intelligence Agent",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
col1, col2 = st.columns([1, 6])
with col1:
    st.image(
        "https://www.gartner.com/pi/vendorimages/compunnel_1697620403838.png",
        width=90
    )
with col2:
    st.markdown("""
    <h1>Career & Skills Intelligence Platform</h1>
    <h4 style='color:gray'>Enterprise Career Agent • HR & Manager Decisions</h4>
    """, unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.header("Configuration")

view_mode = st.sidebar.selectbox("View Mode", ["Manager", "HR"])

uploaded_file = st.sidebar.file_uploader(
    "Upload Employee CSV",
    type="csv"
)

df = pd.read_csv(uploaded_file) if uploaded_file else None

if df is not None:
    selected_emp = st.sidebar.selectbox(
        "Select Employee",
        df["name"].unique()
    )
    emp = df[df["name"] == selected_emp].iloc[0]
else:
    emp = {}

# --------------------------------------------------
# INPUT DATA
# --------------------------------------------------
name = emp.get("name", st.sidebar.text_input("Name"))
role = emp.get("role", st.sidebar.text_input("Current Role"))
target_role = emp.get("target_role", st.sidebar.text_input("Target Role"))
experience = int(emp.get("experience", st.sidebar.number_input("Experience (years)", 0, 40)))
skills = emp.get("skills", st.sidebar.text_area("Skills (comma separated)"))
certifications = emp.get("certifications", st.sidebar.text_area("Certifications (if any)"))

skill_list = [s.strip() for s in skills.split(",") if s.strip()]

# --------------------------------------------------
# SELF-ASSESSMENT (CRITICAL FIX)
# --------------------------------------------------
st.sidebar.subheader("Self-Assessment (Optional)")

self_confidence = st.sidebar.selectbox(
    "Overall Skill Confidence",
    ["Foundational", "Working Professional", "Advanced", "Expert"]
)

ownership_level = st.sidebar.selectbox(
    "Primary Responsibility Level",
    [
        "Execution-focused (guided work)",
        "Independent contributor",
        "Feature / module owner",
        "End-to-end system owner"
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
# ROLE-AWARE SCORING (USED ONLY FOR VISUALS)
# --------------------------------------------------
ROLE_PROFILES = {
    "HR": ["Recruitment", "HRMS", "Compliance", "Employee Relations", "Policy"],
    "DATA": ["Python", "ML", "AI", "SQL", "Statistics", "NLP"],
    "GENERIC": []
}

def detect_role_type(role):
    r = role.upper()
    if "HR" in r:
        return "HR"
    if "DATA" in r or "SCIENTIST" in r:
        return "DATA"
    return "GENERIC"

def compute_scores(role, skills, experience):
    role_type = detect_role_type(role)
    core = ROLE_PROFILES.get(role_type, [])

    skill_match = sum(
        1 for s in skills if any(c.lower() in s.lower() for c in core)
    )

    readiness = min(55 + skill_match * 6 + experience * 3, 95)
    promotion = int(readiness * 0.85)

    return readiness, promotion

career_readiness, promotion_score = compute_scores(
    role,
    skill_list,
    experience
)

peer_percentile = max(55, min(95, 60 + (career_readiness - 55)))

# --------------------------------------------------
# GROQ CAREER AGENT PROMPT (FIXED)
# --------------------------------------------------
def generate_insights():
    prompt = f"""
You are a **Senior Enterprise HR Career Intelligence Agent**.

This report is used by:
- HR partners
- Promotion committees
- Business leadership

--------------------------------------------------
EMPLOYEE PROFILE
--------------------------------------------------
Name: {name}
Current Role: {role}
Target Role: {target_role}
Experience: {experience} years
Skills: {skills}
Certifications: {certifications}

--------------------------------------------------
SELF-ASSESSMENT (USER PROVIDED)
--------------------------------------------------
Overall Skill Confidence: {self_confidence}
Responsibility Level: {ownership_level}

--------------------------------------------------
INTERNAL CONTEXT (DO NOT SCORE SKILLS NUMERICALLY)
--------------------------------------------------
Career Readiness Indicator: {career_readiness}/100
Promotion Indicator: {promotion_score}/100
Peer Percentile Estimate: Top {peer_percentile}%

--------------------------------------------------
STRICT GUIDELINES
--------------------------------------------------
- DO NOT use numeric skill ratings (no 1–5, no percentages)
- DO NOT sound judgmental
- Use professional descriptors only:
  "Strong working proficiency", "Applied exposure",
  "Developing depth", "Foundational familiarity"
- Validate self-assessment; do NOT override it
- Promotion decisions must be strategic, not harsh
- No technical certifications for HR roles
- No leadership fluff for technical roles unless justified

--------------------------------------------------
DELIVERABLES
--------------------------------------------------

### 1️⃣ Executive Career Overview
### 2️⃣ Skills & Capability Assessment (descriptor-based)
### 3️⃣ Role-Relevant Certification Strategy (or explain why not required)
### 4️⃣ Career Progression Path
### 5️⃣ Readiness vs Promotion Explanation (strategic framing)
### 6️⃣ Promotion Readiness Statement
Use ONLY:
- Promotion Ready
- Conditionally Ready
- Progressing Toward Readiness

### 7️⃣ Peer Benchmark Summary
### 8️⃣ Career Improvement Roadmap
(0–6, 6–12, 12–24 months)

### 9️⃣ HR Approval Notes
### 🔟 Career Summary & Improvement Path

--------------------------------------------------
OUTPUT STYLE
--------------------------------------------------
- Executive tone
- HR-safe language
- Markdown headings
- Clear, defensible statements
- NO generic AI phrasing
"""

    return career_agent(prompt)

# --------------------------------------------------
# VISUALS (DESCRIPTIVE, NOT JUDGMENTAL)
# --------------------------------------------------
def create_skill_coverage_plot():
    role_type = detect_role_type(role)
    required = set(ROLE_PROFILES.get(role_type, []))
    available = set(skill_list)

    covered = list(required & available)
    missing = list(required - available)

    fig, ax = plt.subplots()
    ax.barh(covered, [1]*len(covered), label="Aligned Skills")
    ax.barh(missing, [1]*len(missing), label="Development Areas")
    ax.set_title("Role Skill Alignment Overview")
    ax.legend()
    ax.set_xticks([])
    return fig

def create_readiness_plot():
    fig, ax = plt.subplots()
    ax.bar(
        ["Career Readiness", "Promotion Indicator"],
        [career_readiness, promotion_score]
    )
    ax.set_ylim(0, 100)
    ax.set_title("Career Positioning Overview")
    return fig

# --------------------------------------------------
# PDF GENERATION (EXECUTIVE)
# --------------------------------------------------
def generate_pdf(insights_md):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionHeader",
        backColor=colors.HexColor("#1f4fd8"),
        textColor=colors.white,
        padding=8,
        spaceAfter=10
    ))

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(file.name, pagesize=A4)

    story = []

    # SUMMARY PAGE
    story.append(Paragraph("Career Intelligence Report", styles["Title"]))
    story.append(Spacer(1, 12))

    summary_table = Table([
        ["Employee", name],
        ["Current Role", role],
        ["Target Role", target_role],
        ["Experience", f"{experience} Years"],
        ["Career Readiness", "Progressing Well"],
        ["Promotion Status", "Strategic Readiness Review"],
        ["Peer Positioning", f"Top {peer_percentile}%"],
        ["Approval Status", approval_status]
    ], colWidths=[180, 300])

    summary_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.grey),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold")
    ]))

    story.append(summary_table)
    story.append(PageBreak())

    # INSIGHTS
    for line in insights_md.split("\n"):
        if line.strip():
            story.append(Paragraph(line, styles["Normal"]))

    story.append(PageBreak())

    # VISUALS
    skill_img = BytesIO()
    readiness_img = BytesIO()

    create_skill_coverage_plot().savefig(skill_img, format="png")
    create_readiness_plot().savefig(readiness_img, format="png")

    skill_img.seek(0)
    readiness_img.seek(0)

    story.append(Paragraph("Visual Career Overview", styles["Heading1"]))
    story.append(Image(skill_img, width=400, height=250))
    story.append(Spacer(1, 20))
    story.append(Image(readiness_img, width=400, height=250))

    doc.build(story)
    return file.name

# --------------------------------------------------
# UI ACTION
# --------------------------------------------------
if st.button("Run Career Analysis"):
    insights = generate_insights()
    st.markdown(insights)

    colA, colB = st.columns(2)
    colA.metric("Career Readiness", "Progressing Well")
    colB.metric("Promotion Outlook", "Strategic Review")

    colA.pyplot(create_skill_coverage_plot())
    colB.pyplot(create_readiness_plot())

    if approval_status == "Approved":
        pdf_path = generate_pdf(insights)
        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download Full Career Report (PDF)",
                f,
                file_name=f"{name}_Career_Report.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("PDF download enabled only after HR approval.")

st.info("Enterprise Career Intelligence Agent • Compunnel")
