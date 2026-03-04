# Amar Passport — বাংলাদেশ ই-পাসপোর্ট আবেদন প্রস্তুতি

A comprehensive Bangladesh E-Passport application readiness portal that helps citizens check eligibility, calculate fees, and prepare the required documents — all in one place.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54%2B-FF4B4B?logo=streamlit&logoColor=white)

---

## Features

| Feature | Description |
|---|---|
| **Eligibility Check** | Instantly determine passport validity (5 / 10 years) by age |
| **Fee Calculator** | Official 2026 fee schedule with 15% VAT — 48 & 64 page options |
| **Document Checklist** | Customized per applicant type (adult, minor, govt, private sector) |
| **Detailed Report** | Full readiness report in English & Bangla with warnings |
| **Fee Reference** | Complete fee schedule table for all combinations |
| **FAQ** | Common questions answered at a glance |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A [Hugging Face API token](https://huggingface.co/settings/tokens)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/saminul-amin/amar-passport.git
   cd amar-passport
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   ```

   Activate it:

   - **Windows:** `.venv\Scripts\activate`
   - **macOS / Linux:** `source .venv/bin/activate`

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Copy the example file and add your Hugging Face token:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   ```
   HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
   ```

### Running the App

**Web UI (Streamlit):**

```bash
streamlit run app.py
```

**CLI mode:**

```bash
python amar_passport.py
```

---

## Fee Structure (2026)

All fees include **15% VAT**.

### 48-Page Passport

| Validity | Regular | Express | Super Express |
|---|---|---|---|
| 5 Years | ৳ 4,025 | ৳ 6,325 | ৳ 8,625 |
| 10 Years | ৳ 5,750 | ৳ 8,050 | ৳ 10,350 |

### 64-Page Passport

| Validity | Regular | Express | Super Express |
|---|---|---|---|
| 5 Years | ৳ 6,325 | ৳ 8,625 | ৳ 12,075 |
| 10 Years | ৳ 8,050 | ৳ 10,350 | ৳ 13,800 |

## Eligibility Rules

| Age Group | Max Validity | Required ID |
|---|---|---|
| Under 18 | 5 Years | Birth Registration (English) |
| 18–65 | 10 Years | NID Card |
| Over 65 | 5 Years | NID Card |

---

## Disclaimer

This portal is an **application preparation tool** only. It does **not** submit passport applications to the Bangladesh Department of Immigration & Passports. Fee data is based on the officially published 2026 schedule. Always verify with the [official e-Passport portal](https://www.epassport.gov.bd) before applying.

---

## Contact

**Md. Saminul Amin**

- GitHub: [@saminul-amin](https://github.com/saminul-amin)
- LinkedIn: [@Md. Saminul Amin](https://www.linkedin.com/in/md-saminul-amin/)

Have questions, suggestions, or found a bug? Feel free to [open an issue](https://github.com/saminul-amin/amar-passport/issues) — I promise I read them faster than the passport office processes applications.

<!-- This readme file is made using AI -->

