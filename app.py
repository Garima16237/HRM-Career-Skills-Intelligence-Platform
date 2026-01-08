import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, PageBreak
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

view_mode = st.sidebar.selectbox(
    "View Mode",
    ["Manager", "HR"]
)

uploaded_file = st.sidebar.file_uploader(
    "Upload Employee CSV",
    type="csv"
)

df = pd.read_csv(uploaded_file) if uploaded_file else None

# --------------------------------------------------
# EMPLOYEE SELECTION (EMPLOYEE ID PRIMARY)
# --------------------------------------------------
if df is not None and "employee_id" in df.columns:
    selected_emp_id = st.sidebar.selectbox(
        "Select Employee ID",
        df["employee_id"].astype(str).unique()
    )
    emp = df[df["employee_id"].astype(str) == selected_emp_id].iloc[0]
else:
    emp = {}

# --------------------------------------------------
# INPUT DATA
# --------------------------------------------------
employee_id = emp.get("employee_id", st.sidebar.text_input("Employee ID"))
name = emp.get("name", st.sidebar.text_input("Employee Name"))
role = emp.get("role", st.sidebar.text_input("Current Role"))
target_role = emp.get("target_role", st.sidebar.text_input("Target Role"))
experience = int(emp.get("experience", st.sidebar.number_input("Experience (years)", 0, 40)))
skills = emp.get("skills", st.sidebar.text_area("Skills (comma separated)"))
certifications = emp.get("certifications", st.sidebar.text_area("Certifications (if any)"))

skill_list = [s.strip() for s in skills.split(",") if s.strip()]

# --------------------------------------------------
# SELF-ASSESSMENT
# --------------------------------------------------
st.sidebar.subheader("Self-Assessment")

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
# ROLE-AWARE SCORING (INTERNAL ONLY)
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
    skill_match = sum(1 for s in skills if any(c.lower() in s.lower() for c in core))

    readiness = min(60 + skill_match * 5 + experience * 3, 92)
    promotion = int(readiness * 0.85)
    return readiness, promotion

career_readiness, promotion_score = compute_scores(
    role, skill_list, experience
)

peer_percentile = max(60, min(95, 65 + (career_readiness - 60)))

# --------------------------------------------------
# GROQ PROMPT (EXECUTIVE-GRADE)
# --------------------------------------------------
def generate_insights():
    prompt = f"""
You are a Senior Enterprise HR Career Intelligence Agent.

This report is reviewed by:
• HR Business Partners
• Promotion Committees
• Leadership

EMPLOYEE IDENTIFICATION
Employee ID: {employee_id}
Employee Name: {name}

ROLE CONTEXT
Current Role: {role}
Target Role: {target_role}
Experience: {experience} years

SKILLS (Self-Declared):
{skills}

CERTIFICATIONS:
{certifications}

SELF-ASSESSMENT
Confidence Level: {self_confidence}
Responsibility Scope: {ownership_level}

INTERNAL CONTEXT (DO NOT EXPOSE NUMERIC SCORES)
Career Readiness Indicator: {career_readiness}
Promotion Indicator: {promotion_score}
Peer Positioning: Top {peer_percentile}%

STRICT RULES
- No numeric skill ratings
- No judgmental language
- No generic advice
- Frame gaps as scope expansion
- Promotion logic must be strategic and fair
- Use executive HR tone

MANDATORY SECTIONS
### Executive Career Overview
### Skills & Capability Assessment
### Role-Relevant Certification Strategy
### Career Progression Path
### Career Readiness vs Promotion Eligibility
### Promotion Readiness Statement
(Only: Promotion Ready / Conditionally Ready / Progressing Toward Readiness)
### Peer Benchmark Summary
### Career Improvement Roadmap (0–6, 6–12, 12–24 months)
### HR Approval Notes
### Career Summary & Improvement Path

Write like a Senior HR Partner preparing a promotion review.
"""
    return career_agent(prompt)

# --------------------------------------------------
# VISUALS (SUPPORTIVE)
# --------------------------------------------------
def create_readiness_plot():
    fig, ax = plt.subplots()
    ax.bar(
        ["Career Readiness", "Promotion Trajectory"],
        [career_readiness, promotion_score]
    )
    ax.set_ylim(0, 100)
    ax.set_title("Career Positioning Overview")
    return fig

# --------------------------------------------------
# PDF GENERATION (FIXED + PROFESSIONAL)
# --------------------------------------------------
def generate_pdf(insights_md):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=13,
        textColor=colors.HexColor("#1f4fd8"),
        spaceAfter=8
    ))

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(file.name, pagesize=A4)
    story = []

    # COVER SUMMARY
    story.append(Paragraph("Career Intelligence Report", styles["Title"]))
    story.append(Spacer(1, 14))

    summary_table = Table([
        ["Employee ID", employee_id],
        ["Employee Name", name],
        ["Current Role", role],
        ["Target Role", target_role],
        ["Experience", f"{experience} years"],
        ["Peer Positioning", f"Top {peer_percentile}%"],
        ["Approval Status", approval_status]
    ], colWidths=[180, 320])

    summary_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold")
    ]))

    story.append(summary_table)
    story.append(PageBreak())

    # INSIGHTS (SECTION-AWARE)
    for section in insights_md.split("###"):
        if section.strip():
            title, *body = section.split("\n")
            story.append(Paragraph(title.strip(), styles["SectionHeader"]))
            for line in body:
                if line.strip():
                    story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 12))

    story.append(PageBreak())

    # VISUAL
    img = BytesIO()
    create_readiness_plot().savefig(img, format="png")
    img.seek(0)

    story.append(Paragraph("Career Positioning Snapshot", styles["Heading2"]))
    story.append(Image(img, width=400, height=250))

    doc.build(story)
    return file.name

# --------------------------------------------------
# UI ACTION
# --------------------------------------------------
if st.button("Run Career Analysis"):
    insights = generate_insights()

    # EXECUTIVE DISPLAY
    st.subheader("Executive Career Review")
    st.markdown(insights)

    colA, colB = st.columns(2)
    colA.metric("Career Trajectory", "Progressing Well")
    colB.metric("Promotion Outlook", "Strategic Review")

    colA.pyplot(create_readiness_plot())

    if approval_status == "Approved":
        pdf_path = generate_pdf(insights)
        with open(pdf_path, "rb") as f:
            st.download_button(
                "📄 Download Career Report (PDF)",
                f,
                file_name=f"{employee_id}_Career_Report.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("PDF download available only after HR approval.")

st.info("Enterprise Career Intelligence Agent • Compunnel")
