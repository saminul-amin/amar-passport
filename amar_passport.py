import os
import sys
import json
import logging
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()

logging.getLogger().setLevel(logging.CRITICAL)
for name in ["crewai", "litellm", "openai", "httpx", "httpcore"]:
    logging.getLogger(name).setLevel(logging.CRITICAL)

if not os.environ.get("HUGGINGFACEHUB_API_TOKEN"):
    print("ERROR: Missing HUGGINGFACEHUB_API_TOKEN. Create a .env file with your token.")
    sys.exit(1)

llm = LLM(
    model="huggingface/Qwen/Qwen2.5-72B-Instruct",
    api_key=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    temperature=0.1,
    max_tokens=2048,
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
        "adult": ["NID Card", "Application Summary", "Payment Slip", "2 copies of Passport-size Photo"],
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
        "name_change": ["Marriage Certificate / Gazette Notification", "NID Card"],
    },
    "delivery_types": {
        "regular": "15-21 working days",
        "express": "7-10 working days",
        "super_express": "2-3 working days",
    },
}


@tool("FeeDatabase")
def query_fee_database(page_count: str, validity: str, delivery_type: str) -> str:
    """Look up the 2026 passport fee. page_count: '48'/'64', validity: '5'/'10', delivery_type: 'regular'/'express'/'super_express'."""
    try:
        pages_key = f"{page_count}_pages"
        years_key = f"{validity}_years"
        fee = local_db["fees_2026"][pages_key][years_key][delivery_type]
        return json.dumps({
            "fee_bdt": fee,
            "page_count": page_count,
            "validity_years": validity,
            "delivery_type": delivery_type,
            "vat_included": True,
            "vat_percentage": 15,
            "delivery_timeline": local_db["delivery_types"].get(delivery_type, "Unknown"),
        })
    except KeyError as e:
        return json.dumps({
            "error": f"Invalid combination. Key not found: {e}",
            "valid_pages": ["48", "64"],
            "valid_validity": ["5", "10"],
            "valid_delivery": ["regular", "express", "super_express"],
        })


@tool("DocumentChecklist")
def query_document_checklist(applicant_type: str) -> str:
    """Retrieve required documents. applicant_type: 'adult'/'minor_under_18'/'government_staff'/'private_sector'/'name_change'."""
    try:
        docs = local_db["required_docs"].get(applicant_type)
        if docs is None:
            return json.dumps({
                "error": f"Unknown applicant type: {applicant_type}",
                "valid_types": list(local_db["required_docs"].keys()),
            })
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
        return json.dumps({
            "age": age,
            "category": category,
            "max_validity": rules["max_validity"],
            "id_required": rules["id_required"],
            "notes": rules["notes"],
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


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


def get_user_profile() -> str:
    print("=" * 60)
    print("AMAR PASSPORT — Virtual Consular Officer")
    print("=" * 60)
    print("\nDescribe your passport needs in one sentence.")
    print("Include your age, profession, page count (48/64),")
    print("urgency (regular/urgent/super urgent), and ID type.\n")
    print('Example: "I am a 24-year-old private sector employee.')
    print("I need a 64-page passport urgently because I have a")
    print('business trip in two weeks. I have an NID and I live in Dhaka."\n')
    user_input = input("Enter your profile: ").strip()
    if not user_input:
        user_input = (
            "I am a 24-year-old private sector employee. I need a 64-page passport "
            "urgently because I have a business trip in two weeks. I have an NID and "
            "I live in Dhaka."
        )
        print("(No input provided, using default profile)")
    return user_input


def build_tasks(user_profile: str):
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


if __name__ == "__main__":
    user_profile = get_user_profile()
    print(f"\nYour Profile: {user_profile}\n")
    print("-" * 60)

    tasks = build_tasks(user_profile)

    passport_crew = Crew(
        agents=[policy_guardian, fee_calculator, document_architect],
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )

    print("\nProcessing your passport application...\n")

    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        result = passport_crew.kickoff()
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout

    raw_output = str(result)
    if len(raw_output.strip()) < 20:
        print("Insufficient information was provided to generate a complete report.")
        print("Please re-run and include your age, profession, page count (48/64),")
        print("urgency level, and ID type in your profile description.")
    else:
        print(raw_output)
