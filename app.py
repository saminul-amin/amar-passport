import os
import sys
import json
import logging
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

logging.getLogger().setLevel(logging.CRITICAL)
for _name in ["crewai", "litellm", "openai", "httpx", "httpcore"]:
    logging.getLogger(_name).setLevel(logging.CRITICAL)

if not os.environ.get("HUGGINGFACEHUB_API_TOKEN"):
    st.error("Missing HUGGINGFACEHUB_API_TOKEN. Please set it in a .env file.")
    st.stop()

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

st.set_page_config(
    page_title="Amar Passport — বাংলাদেশ ই-পাসপোর্ট সেবা",
    page_icon="🛂",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# AI helped with this part! I am poor here! Additionally I got ideas from AI as well!
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Header banner */
    .portal-header {
        background: linear-gradient(135deg, #006a4e 0%, #004d3a 100%);
        color: white;
        padding: 2rem 2rem 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,106,78,0.25);
    }
    .portal-header h1 {
        margin: 0 0 0.25rem 0;
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .portal-header .subtitle {
        font-size: 0.95rem;
        opacity: 0.9;
        font-weight: 400;
    }
    .portal-header .bangla {
        font-size: 1.1rem;
        margin-top: 0.3rem;
        opacity: 0.85;
    }

    /* Section cards */
    .section-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .section-card h3 {
        color: #006a4e;
        margin-top: 0;
        font-size: 1.1rem;
        border-bottom: 2px solid #006a4e;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    /* Result cards */
    .result-card {
        background: linear-gradient(to bottom right, #f0fdf4, #ffffff);
        border-left: 4px solid #006a4e;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.75rem 0;
    }
    .result-card h4 {
        color: #006a4e;
        margin-top: 0;
    }

    /* Warning card */
    .warning-card {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }

    /* Fee highlight */
    .fee-highlight {
        background: #006a4e;
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .fee-highlight small {
        display: block;
        font-size: 0.75rem;
        font-weight: 400;
        opacity: 0.85;
        margin-top: 0.25rem;
    }

    /* Footer */
    .portal-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.78rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #e5e7eb;
        margin-top: 2rem;
    }

    /* Streamlit overrides */
    .stButton > button {
        background: linear-gradient(135deg, #006a4e, #004d3a);
        color: white;
        border: none;
        padding: 0.65rem 2.5rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #004d3a, #003a2c);
        box-shadow: 0 4px 12px rgba(0,106,78,0.3);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Table styling */
    .report-table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.75rem 0;
        font-size: 0.92rem;
    }
    .report-table th {
        background: #006a4e;
        color: white;
        padding: 0.6rem 1rem;
        text-align: left;
        font-weight: 600;
    }
    .report-table td {
        padding: 0.55rem 1rem;
        border-bottom: 1px solid #e5e7eb;
    }
    .report-table tr:nth-child(even) {
        background: #f9fafb;
    }
    .report-table tr:hover {
        background: #f0fdf4;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-eligible {
        background: #dcfce7;
        color: #166534;
    }
    .badge-warning {
        background: #fef3c7;
        color: #92400e;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


local_db = {
    "fees_2026": {
        "48_pages": {
            "5_years": {"regular": 4025, "express": 6325, "super_express": 8625},
            "10_years": {"regular": 5750, "express": 8050, "super_express": 10350},
        },
        "64_pages": {
            "5_years": {"regular": 6325, "express": 8625, "super_express": 12075},
            "10_years": {"regular": 8050, "express": 10350, "super_express": 13800},
        },
    },
    "vat_percentage": 15,
    "note": "All fees already include 15% VAT as per 2026 official fee structure.",
    "eligibility_rules": {
        "under_18": {
            "max_validity": "5_years",
            "id_required": "Birth Registration (English)",
            "notes": "Minors cannot get 10-year passports. Parent's NID is also required.",
        },
        "18_to_65": {
            "max_validity": "10_years",
            "id_required": "NID Card",
            "notes": "Standard adult applicant. Both 5-year and 10-year allowed.",
        },
        "over_65": {
            "max_validity": "5_years",
            "id_required": "NID Card",
            "notes": "Senior citizens cannot get 10-year passports.",
        },
    },
    "required_docs": {
        "adult": [
            "NID Card",
            "Application Summary",
            "Payment Slip",
            "2 copies of Passport-size Photo",
        ],
        "minor_under_18": [
            "Birth Registration (English)",
            "Parents' NID (both)",
            "3R size Photo (3 copies)",
            "Application Summary",
            "Payment Slip",
        ],
        "government_staff": [
            "GO (Government Order) / NOC (No Objection Certificate)",
            "NID Card",
            "Service ID Card",
            "Application Summary",
            "Payment Slip",
        ],
        "private_sector": [
            "NID Card",
            "Profession Proof / Employment Certificate",
            "Application Summary",
            "Payment Slip",
            "2 copies of Passport-size Photo",
        ],
        "name_change": [
            "Marriage Certificate / Gazette Notification",
            "NID Card",
        ],
    },
    "delivery_types": {
        "regular": "15–21 working days",
        "express": "7–10 working days",
        "super_express": "2–3 working days",
    },
}


@tool("FeeDatabase")
def query_fee_database(page_count: str, validity: str, delivery_type: str) -> str:
    """Look up the 2026 passport fee. page_count: '48'/'64', validity: '5'/'10', delivery_type: 'regular'/'express'/'super_express'."""
    try:
        pages_key = f"{page_count}_pages"
        years_key = f"{validity}_years"
        fee = local_db["fees_2026"][pages_key][years_key][delivery_type]
        return json.dumps(
            {
                "fee_bdt": fee,
                "page_count": page_count,
                "validity_years": validity,
                "delivery_type": delivery_type,
                "vat_included": True,
                "vat_percentage": 15,
                "delivery_timeline": local_db["delivery_types"].get(
                    delivery_type, "Unknown"
                ),
            }
        )
    except KeyError as e:
        return json.dumps(
            {
                "error": f"Invalid combination. Key not found: {e}",
                "valid_pages": ["48", "64"],
                "valid_validity": ["5", "10"],
                "valid_delivery": ["regular", "express", "super_express"],
            }
        )


@tool("DocumentChecklist")
def query_document_checklist(applicant_type: str) -> str:
    """Retrieve required documents. applicant_type: 'adult'/'minor_under_18'/'government_staff'/'private_sector'/'name_change'."""
    try:
        docs = local_db["required_docs"].get(applicant_type)
        if docs is None:
            return json.dumps(
                {
                    "error": f"Unknown applicant type: {applicant_type}",
                    "valid_types": list(local_db["required_docs"].keys()),
                }
            )
        return json.dumps({"applicant_type": applicant_type, "documents": docs})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("EligibilityRules")
def query_eligibility_rules(age: int) -> str:
    """Retrieve eligibility rules based on age. Returns validity limits and required ID."""
    try:
        age = int(age)
        if age < 18:
            category = "under_18"
        elif age > 65:
            category = "over_65"
        else:
            category = "18_to_65"
        rules = local_db["eligibility_rules"][category]
        return json.dumps(
            {
                "age": age,
                "category": category,
                "max_validity": rules["max_validity"],
                "id_required": rules["id_required"],
                "notes": rules["notes"],
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@st.cache_resource
def get_llm():
    return LLM(
        model="huggingface/Qwen/Qwen2.5-72B-Instruct",
        api_key=os.environ["HUGGINGFACEHUB_API_TOKEN"],
        temperature=0.1,
        max_tokens=2048,
    )


def create_processing_agents(llm):
    policy_guardian = Agent(
        role="Bangladesh Passport Policy Expert",
        goal=(
            "Determine the permitted passport validity (5 vs 10 years) and required "
            "identification document (NID vs Birth Registration) based on the applicant's "
            "age. Strictly FLAG any inconsistencies, for example if a minor (under 18) "
            "or a senior citizen (over 65) requests a 10-year passport."
        ),
        backstory=(
            "You are 'The Policy Guardian', a strict but fair Virtual Consular Officer "
            "with 20 years of experience at the Bangladesh Passport Office. You have "
            "memorized every rule in the Bangladesh E-Passport Ordinance. You know that "
            "applicants under 18 or over 65 can ONLY get 5-year validity passports. "
            "If anyone requests a 10-year passport but is ineligible, you immediately "
            "raise a RED FLAG with a clear warning. You always use the EligibilityRules "
            "tool to verify the rules from the official database before making any decision."
        ),
        verbose=False,
        allow_delegation=False,
        tools=[query_eligibility_rules],
        llm=llm,
    )

    fee_calculator = Agent(
        role="Financial Auditor for Passport Fees",
        goal=(
            "Calculate the exact passport fee in BDT (including 15% VAT) based on "
            "the approved page count, validity period, and delivery speed using the "
            "official 2026 fee structure. Always use the FeeDatabase tool."
        ),
        backstory=(
            "You are 'The Chancellor of the Exchequer', the chief financial officer "
            "of the Passport Office. You are obsessed with numerical accuracy down to "
            "the last taka. You ALWAYS consult the FeeDatabase tool to retrieve the "
            "exact 2026 fee (which already includes 15% VAT). You clearly state the "
            "page count, validity, delivery type, and final amount. You NEVER guess fees."
        ),
        verbose=False,
        allow_delegation=False,
        tools=[query_fee_database],
        llm=llm,
    )

    document_architect = Agent(
        role="Documentation Officer & Report Compiler",
        goal=(
            "Generate a customized document checklist based on age, profession, and "
            "policy. Then compile the final Passport Readiness Report as a Markdown "
            "table in both English and Bangla."
        ),
        backstory=(
            "You are 'The Document Architect', a meticulous documentation specialist "
            "who has processed over 50,000 passport applications. You use the "
            "DocumentChecklist tool to fetch the exact list of required documents for "
            "each applicant type (adult, minor, government staff, private sector). "
            "You compile everything into a professional Passport Readiness Report, "
            "formatted as a Markdown table in English and translated to Bangla."
        ),
        verbose=False,
        allow_delegation=False,
        tools=[query_document_checklist],
        llm=llm,
    )

    return policy_guardian, fee_calculator, document_architect


def build_tasks(user_profile, policy_guardian, fee_calculator, document_architect):
    eligibility_task = Task(
        description=(
            f"Analyze the following user profile and determine passport eligibility:\n\n"
            f"USER PROFILE: '{user_profile}'\n\n"
            f"Steps:\n"
            f"1. Extract the applicant's age from the profile.\n"
            f"2. Use the EligibilityRules tool with the age to get official rules.\n"
            f"3. Determine the APPROVED validity period (5 or 10 years).\n"
            f"4. Determine the required ID document (NID or Birth Registration).\n"
            f"5. If the applicant requests a validity they are NOT eligible for "
            f"(e.g., a 15-year-old asking for 10 years), you MUST flag this as:\n"
            f"   'FLAG: [Reason for inconsistency]'\n"
            f"6. Recommend the correct validity if the requested one is not allowed."
        ),
        expected_output=(
            "A clear summary containing:\n"
            "- Applicant Age\n"
            "- Requested Validity (if any)\n"
            "- Approved Validity (5 or 10 years)\n"
            "- Required ID Type (NID / Birth Registration)\n"
            "- Any WARNING FLAGS about inconsistencies"
        ),
        agent=policy_guardian,
    )

    fee_task = Task(
        description=(
            f"Using the eligibility results from the Policy Guardian AND the user profile below, "
            f"calculate the exact passport fee.\n\n"
            f"USER PROFILE: '{user_profile}'\n\n"
            f"Steps:\n"
            f"1. From the profile, extract: page count and delivery urgency.\n"
            f"   - 'urgently' or 'urgent' means Express delivery\n"
            f"   - 'super urgent' or 'emergency' means Super Express delivery\n"
            f"   - Otherwise means Regular delivery\n"
            f"2. From the Policy Guardian's output, get the APPROVED validity (5 or 10 years).\n"
            f"3. Use the FeeDatabase tool with (page_count, validity, delivery_type) to get the exact fee.\n"
            f"4. Report the fee clearly with all parameters."
        ),
        expected_output=(
            "A clear summary containing:\n"
            "- Page Count (48 or 64)\n"
            "- Approved Validity (5 or 10 years)\n"
            "- Delivery Type (Regular / Express / Super Express)\n"
            "- Delivery Timeline\n"
            "- Total Fee in BDT (with 15% VAT included)"
        ),
        agent=fee_calculator,
        context=[eligibility_task],
    )

    compilation_task = Task(
        description=(
            f"Compile the FINAL Passport Readiness Report using all previous results "
            f"and the user profile.\n\n"
            f"USER PROFILE: '{user_profile}'\n\n"
            f"Steps:\n"
            f"1. Determine the applicant type based on age and profession:\n"
            f"   - Under 18: 'minor_under_18'\n"
            f"   - Government employee: 'government_staff'\n"
            f"   - Private sector: 'private_sector'\n"
            f"   - Otherwise: 'adult'\n"
            f"2. Use the DocumentChecklist tool to get the required documents.\n"
            f"3. Compile the final output in this EXACT format (plain text, NOT a table):\n\n"
            f"   Validity: [5 or 10] Years\n"
            f"   Delivery Type: [Regular / Express / Super Express]\n"
            f"   Total Fee: [Amount] BDT\n"
            f"   Documents Needed: [comma-separated list]\n\n"
            f"4. Then also provide a Markdown table version in English and Bangla.\n"
            f"5. Add any warning flags from the Policy Guardian as notes below.\n"
        ),
        expected_output=(
            "The final output MUST contain:\n\n"
            "1. A plain-text summary in this EXACT format:\n"
            "   Validity: [X] Years\n"
            "   Delivery Type: [Type]\n"
            "   Total Fee: [Amount] BDT\n"
            "   Documents Needed: [Doc1, Doc2, Doc3, ...]\n\n"
            "2. A Markdown table with columns: Field | Details\n"
            "3. The same table translated into Bangla\n"
            "4. Any WARNING/FLAG notes at the bottom if applicable"
        ),
        agent=document_architect,
        context=[eligibility_task, fee_task],
    )

    return [eligibility_task, fee_task, compilation_task]


def process_application(user_profile: str) -> str:
    """Run the passport processing engine and return the final report."""
    llm = get_llm()
    policy_guardian, fee_calculator, document_architect = create_processing_agents(llm)
    tasks = build_tasks(user_profile, policy_guardian, fee_calculator, document_architect)

    passport_crew = Crew(
        agents=[policy_guardian, fee_calculator, document_architect],
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )

    # Suppress stdout from the processing engine
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        result = passport_crew.kickoff()
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout

    return str(result)


def quick_fee_lookup(page_count, validity, delivery_type):
    """Direct database fee lookup — fast, no processing required."""
    pages_key = f"{page_count}_pages"
    years_key = f"{validity}_years"
    try:
        return local_db["fees_2026"][pages_key][years_key][delivery_type]
    except KeyError:
        return None


def quick_eligibility(age):
    """Direct eligibility rules lookup."""
    if age < 18:
        return local_db["eligibility_rules"]["under_18"]
    elif age > 65:
        return local_db["eligibility_rules"]["over_65"]
    else:
        return local_db["eligibility_rules"]["18_to_65"]


def get_applicant_type(age, profession):
    """Determine applicant type from age and profession."""
    if age < 18:
        return "minor_under_18"
    prof_lower = profession.lower()
    if any(
        kw in prof_lower
        for kw in ["government", "সরকারি", "sorkari", "govt"]
    ):
        return "government_staff"
    if any(
        kw in prof_lower
        for kw in ["private", "বেসরকারি", "besorkari", "corporate", "business", "ব্যবসা"]
    ):
        return "private_sector"
    return "adult"


def render_header():
    st.markdown(
        """
        <div class="portal-header">
            <h1>Amar Passport</h1>
            <div class="subtitle">Bangladesh E-Passport Application Readiness Portal</div>
            <div class="bangla">বাংলাদেশ ই-পাসপোর্ট আবেদন প্রস্তুতি পোর্টাল</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <div class="portal-footer">
            <strong>Amar Passport</strong> — Passport Application Readiness System<br>
            Fee structure based on Bangladesh Department of Immigration & Passports, 2026.<br>
            This portal helps you prepare your application. It does not submit applications on your behalf.<br>
            © 2026 Amar Passport. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quick_result(age, page_count, validity, delivery_type, profession):
    """Render the fast deterministic result cards."""
    eligibility = quick_eligibility(age)
    max_valid = eligibility["max_validity"]  
    max_years = int(max_valid.split("_")[0])

    has_warning = False
    warning_msg = ""
    approved_validity = validity
    if int(validity) > max_years:
        has_warning = True
        approved_validity = str(max_years)
        if age < 18:
            warning_msg = (
                f"Applicants under 18 are only eligible for 5-year passports. "
                f"Your requested {validity}-year validity has been adjusted to {approved_validity} years."
            )
        else:
            warning_msg = (
                f"Applicants over 65 are only eligible for 5-year passports. "
                f"Your requested {validity}-year validity has been adjusted to {approved_validity} years."
            )

    fee = quick_fee_lookup(page_count, approved_validity, delivery_type)
    timeline = local_db["delivery_types"].get(delivery_type, "Unknown")
    applicant_type = get_applicant_type(age, profession)
    docs = local_db["required_docs"].get(applicant_type, local_db["required_docs"]["adult"])

    delivery_labels = {"regular": "Regular", "express": "Express", "super_express": "Super Express"}

    if has_warning:
        st.markdown(
            f'<div class="warning-card">{warning_msg}</div>',
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="result-card">
                <h4>Eligibility Status</h4>
                <p><strong>Age:</strong> {age} years</p>
                <p><strong>Category:</strong> {"Minor (Under 18)" if age < 18 else "Senior Citizen (65+)" if age > 65 else "Adult (18–65)"}</p>
                <p><strong>Status:</strong> <span class="status-badge {"badge-warning" if has_warning else "badge-eligible"}">
                    {"Adjusted" if has_warning else "Eligible"}</span></p>
                <p><strong>Approved Validity:</strong> {approved_validity} Years</p>
                <p><strong>Required ID:</strong> {eligibility["id_required"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="result-card">
                <h4>Fee Breakdown</h4>
                <p><strong>Page Count:</strong> {page_count} pages</p>
                <p><strong>Validity:</strong> {approved_validity} Years</p>
                <p><strong>Delivery:</strong> {delivery_labels.get(delivery_type, delivery_type)}</p>
                <p><strong>Timeline:</strong> {timeline}</p>
                <p><strong>VAT:</strong> 15% (included)</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Fees
    if fee:
        st.markdown(
            f"""
            <div class="fee-highlight">
                ৳ {fee:,} BDT
                <small>Total Fee (15% VAT Included)</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Doc table
    st.markdown("---")
    st.markdown("#### Required Documents / প্রয়োজনীয় কাগজপত্র")

    doc_rows = ""
    for i, doc in enumerate(docs, 1):
        doc_rows += f"<tr><td>{i}</td><td>{doc}</td><td>☐</td></tr>"

    st.markdown(
        f"""
        <table class="report-table">
            <thead>
                <tr><th>#</th><th>Document</th><th>Ready?</th></tr>
            </thead>
            <tbody>
                {doc_rows}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    # Benglai summary table
    bangla_delivery = {"regular": "সাধারণ", "express": "এক্সপ্রেস", "super_express": "সুপার এক্সপ্রেস"}
    bangla_pages = {"48": "৪৮", "64": "৬৪"}
    bangla_validity = {"5": "৫", "10": "১০"}

    st.markdown("#### বাংলায় সারসংক্ষেপ")
    st.markdown(
        f"""
        <table class="report-table">
            <thead>
                <tr><th>বিষয়</th><th>বিবরণ</th></tr>
            </thead>
            <tbody>
                <tr><td>পৃষ্ঠা সংখ্যা</td><td>{bangla_pages.get(page_count, page_count)} পৃষ্ঠা</td></tr>
                <tr><td>মেয়াদ</td><td>{bangla_validity.get(approved_validity, approved_validity)} বছর</td></tr>
                <tr><td>ডেলিভারি</td><td>{bangla_delivery.get(delivery_type, delivery_type)}</td></tr>
                <tr><td>সময়সীমা</td><td>{timeline}</td></tr>
                <tr><td>মোট ফি</td><td>৳ {fee:,} টাকা (১৫% ভ্যাট সহ)</td></tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    if has_warning:
        st.markdown(
            f"""
            <div class="warning-card">
                <strong>সতর্কতা:</strong> {warning_msg}
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    render_header()

    tab_detailed, tab_quick, tab_fees, tab_faq = st.tabs(
        ["Detailed Report", "Application Check", "Fee Schedule", "FAQ"]
    )

    with tab_quick:
        st.markdown(
            '<div class="section-card"><h3>Applicant Information / আবেদনকারীর তথ্য</h3>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            applicant_name = st.text_input(
                "Full Name / পূর্ণ নাম",
                placeholder="e.g. Md. Rafiqul Islam",
            )
            age = st.number_input(
                "Age / বয়স", min_value=0, max_value=120, value=25, step=1
            )
            profession = st.selectbox(
                "Profession / পেশা",
                [
                    "Private Sector Employee",
                    "Government Employee",
                    "Student",
                    "Business Owner",
                    "Housewife / Homemaker",
                    "Retired",
                    "Unemployed",
                    "Other",
                ],
            )

        with col_b:
            page_count = st.selectbox("Page Count / পৃষ্ঠা সংখ্যা", ["48", "64"])
            validity = st.selectbox("Desired Validity / মেয়াদ", ["5", "10"], index=1)
            delivery_type = st.selectbox(
                "Delivery Speed / ডেলিভারি ধরন",
                ["regular", "express", "super_express"],
                format_func=lambda x: {
                    "regular": "Regular (15–21 days)",
                    "express": "Express (7–10 days)",
                    "super_express": "Super Express (2–3 days)",
                }[x],
            )
            id_type = st.selectbox(
                "ID Type / পরিচয়পত্র",
                ["NID Card", "Birth Registration (English)"],
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button(" Check Application Readiness", key="quick_check"):
            with st.spinner("Verifying eligibility and calculating fees..."):
                render_quick_result(age, page_count, validity, delivery_type, profession)

    with tab_detailed:
        st.markdown(
            '<div class="section-card"><h3>Detailed Application Analysis / বিস্তারিত বিশ্লেষণ</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "Provide a brief description of your passport needs. Our system will analyze "
            "your eligibility, calculate fees, and generate a complete readiness report."
        )

        profile_text = st.text_area(
            "Describe your passport needs / আপনার পাসপোর্টের প্রয়োজনীয়তা লিখুন",
            height=120,
            placeholder=(
                "Example: I am a 24-year-old private sector employee. I need a 64-page "
                "passport urgently because I have a business trip in two weeks. I have "
                "an NID and I live in Dhaka."
            ),
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Generate Detailed Report", key="detailed_report"):
            if not profile_text.strip():
                st.warning("Please describe your passport needs to generate a report.")
            else:
                with st.spinner("Analyzing your application — this may take a moment..."):
                    result = process_application(profile_text.strip())
                    if len(result.strip()) < 20:
                        st.error(
                            "Could not generate a complete report. Please include your "
                            "age, profession, page count (48/64), urgency level, and ID type."
                        )
                    else:
                        st.markdown("---")
                        st.markdown("### Passport Readiness Report")
                        st.markdown(result)

    with tab_fees:
        st.markdown(
            '<div class="section-card"><h3>Official Fee Schedule 2026 / ফি তালিকা ২০২৬</h3>',
            unsafe_allow_html=True,
        )
        st.markdown("All fees include **15% VAT** as per the official 2026 structure.")
        st.markdown("</div>", unsafe_allow_html=True)

        # 48 pages table
        st.markdown("##### 48-Page Passport / ৪৮ পৃষ্ঠা পাসপোর্ট")
        st.markdown(
            """
            <table class="report-table">
                <thead>
                    <tr><th>Validity</th><th>Regular</th><th>Express</th><th>Super Express</th></tr>
                </thead>
                <tbody>
                    <tr><td>5 Years</td><td>৳ 4,025</td><td>৳ 6,325</td><td>৳ 8,625</td></tr>
                    <tr><td>10 Years</td><td>৳ 5,750</td><td>৳ 8,050</td><td>৳ 10,350</td></tr>
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

        # 64 pages table
        st.markdown("##### 64-Page Passport / ৬৪ পৃষ্ঠা পাসপোর্ট")
        st.markdown(
            """
            <table class="report-table">
                <thead>
                    <tr><th>Validity</th><th>Regular</th><th>Express</th><th>Super Express</th></tr>
                </thead>
                <tbody>
                    <tr><td>5 Years</td><td>৳ 6,325</td><td>৳ 8,625</td><td>৳ 12,075</td></tr>
                    <tr><td>10 Years</td><td>৳ 8,050</td><td>৳ 10,350</td><td>৳ 13,800</td></tr>
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("##### Delivery Timelines / ডেলিভারি সময়সীমা")
        st.markdown(
            """
            <table class="report-table">
                <thead>
                    <tr><th>Type</th><th>Timeline</th></tr>
                </thead>
                <tbody>
                    <tr><td>Regular</td><td>15–21 working days</td></tr>
                    <tr><td>Express</td><td>7–10 working days</td></tr>
                    <tr><td>Super Express</td><td>2–3 working days</td></tr>
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

    with tab_faq:
        st.markdown(
            '<div class="section-card"><h3>Frequently Asked Questions / সচরাচর জিজ্ঞাসা</h3>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Can minors (under 18) get a 10-year passport?"):
            st.markdown(
                "**No.** Applicants under 18 are only eligible for **5-year** validity "
                "passports. A Birth Registration certificate (English) is required instead of NID."
            )

        with st.expander("Can senior citizens (over 65) get a 10-year passport?"):
            st.markdown(
                "**No.** Applicants over 65 are restricted to **5-year** validity passports."
            )

        with st.expander("What documents do government employees need?"):
            st.markdown(
                "Government employees need a **GO (Government Order) or NOC (No Objection Certificate)**, "
                "NID Card, Service ID Card, Application Summary, and Payment Slip."
            )

        with st.expander("Are the fees inclusive of VAT?"):
            st.markdown(
                "**Yes.** All fees shown on this portal already include the **15% VAT** "
                "as per the 2026 official fee structure."
            )

        with st.expander("How do I choose between 48 and 64 pages?"):
            st.markdown(
                "Choose **64 pages** if you are a frequent traveler or expect to accumulate "
                "multiple visa stamps. Otherwise, **48 pages** is sufficient for most applicants."
            )

        with st.expander("What is the difference between Express and Super Express?"):
            st.markdown(
                "**Express** delivery takes 7–10 working days, while **Super Express** "
                "takes only 2–3 working days. Super Express is ideal for emergency travel situations."
            )

        with st.expander("Where do I submit my passport application?"):
            st.markdown(
                "Applications are submitted at any **Regional Passport Office** or through "
                "the **online e-passport portal** at [epassport.gov.bd](https://www.epassport.gov.bd). "
                "This portal only helps you prepare — it does not submit applications."
            )

    render_footer()


if __name__ == "__main__":
    main()
