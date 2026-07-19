"""
services/doc_generator.py
Auto-generates a realistic set of hospital policy PDFs the first time the app
runs, so the RAG pipeline has real content to index without requiring the
user to source their own documents.
"""
from __future__ import annotations

from fpdf import FPDF

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# title -> body text. Body uses "\n\n" for paragraph breaks and "- " for bullets.
POLICY_DOCS: dict[str, str] = {
    "Visitor_Policy": """Hospital Visitor Policy

Purpose: To ensure patient safety, privacy, and a restful recovery environment while allowing
meaningful family and social support during a hospital stay.

General Visiting Hours: Visitors are welcome from 9:00 AM to 8:00 PM daily in general wards.
Immediate family members may request extended hours by checking in with the nursing station.

Number of Visitors: A maximum of two visitors per patient is permitted at the bedside at any
one time in general wards. Pediatric and maternity wards allow up to two guardians at all times.

Health Screening: All visitors must complete a brief health screening at the entrance. Anyone
with fever, cough, or other symptoms of a contagious illness will be asked to postpone their
visit and may video call the patient instead.

Minors: Children under 12 must be accompanied by an adult at all times and are not permitted
in the ICU, isolation wards, or the emergency department.

Restricted Areas: Visitors are not permitted in the operating theatre, ICU (outside designated
visiting windows), isolation rooms, or the pharmacy without explicit staff authorization.

Behavior Expectations: Visitors must maintain a quiet environment, avoid bringing large groups,
and follow all instructions from nursing staff, including immediate departure if requested for
a medical procedure or emergency.

Personal Belongings: The hospital is not responsible for personal belongings brought by
visitors or left with patients. Valuables should not be brought to the hospital.
""",
    "ICU_Guidelines": """Intensive Care Unit (ICU) Guidelines

Purpose: To protect critically ill patients from infection and stress while supporting family
involvement in care decisions.

ICU Visiting Windows: Visiting is restricted to two 30-minute windows per day: 11:00 AM-11:30 AM
and 6:00 PM-6:30 PM. Only one visitor is allowed at the bedside at a time.

Entry Requirements: All ICU visitors must sanitize hands, wear a provided gown and mask, and
remove any outdoor jackets before entry. Visitors with recent travel history to areas with
active disease outbreaks may be asked to delay their visit.

Family Communication: A designated family spokesperson will receive daily updates from the
attending physician. This reduces repeated interruptions to clinical staff and ensures
consistent information is shared with the family.

Devices and Phones: Mobile phones must be silenced. Photography or video recording of any
patient, equipment, or staff is strictly prohibited without written consent.

End-of-Life Situations: Exceptions to visiting hours and visitor limits are made for patients
in critical or end-of-life situations, at the discretion of the charge nurse and attending
physician.

Equipment Safety: Visitors must not touch, adjust, or lean on any medical equipment, monitors,
or IV lines under any circumstances.
""",
    "Admission_SOP": """Patient Admission Standard Operating Procedure

Purpose: To standardize the process for admitting patients safely, accurately, and efficiently.

Step 1 - Registration: Front desk staff verify patient identity using government-issued ID and
insurance details, and create or update the patient's record in the hospital information system.

Step 2 - Triage Assessment: A triage nurse records vital signs, chief complaint, and assigns an
urgency level (Emergency, Urgent, or Elective) which determines the admission pathway.

Step 3 - Bed Assignment: The bed management team assigns a room based on the patient's
condition, required department (e.g., ICU, general ward, maternity), and isolation needs.

Step 4 - Clinical Handover: The admitting physician reviews history, current medications, and
allergies, and documents an initial care plan within two hours of admission.

Step 5 - Consent and Documentation: Patients or their legal guardians sign consent forms for
treatment, and are provided a copy of the Patient Rights and Privacy Policy.

Step 6 - Orientation: Nursing staff orient the patient and family to the room, call button,
visiting hours, and meal schedule.

Emergency Admissions: Life-threatening cases bypass standard registration and are admitted
immediately, with paperwork completed retrospectively once the patient is stabilized.
""",
    "Discharge_SOP": """Patient Discharge Standard Operating Procedure

Purpose: To ensure a safe, well-documented, and well-communicated transition from hospital
care back to the patient's home or another care facility.

Step 1 - Discharge Readiness Review: The attending physician confirms the patient meets
clinical discharge criteria (stable vital signs, controlled symptoms, safe mobility).

Step 2 - Medication Reconciliation: The pharmacy team reviews all prescribed medications,
provides a discharge medication list, and counsels the patient on dosage and interactions.

Step 3 - Discharge Summary: The physician prepares a discharge summary covering diagnosis,
treatment provided, follow-up instructions, and any red-flag symptoms to watch for.

Step 4 - Follow-Up Scheduling: Administrative staff schedule any required follow-up
appointments before the patient leaves and provide referral letters if needed.

Step 5 - Billing Clearance: The billing office finalizes charges and processes insurance
claims or provides an itemized invoice for self-pay patients.

Step 6 - Physical Discharge: Nursing staff remove any lines or devices, provide discharge
paperwork, and escort the patient to the exit or transport service.

Same-Day Discharge Target: The hospital aims to complete the full discharge process within
four hours of a physician's discharge order.
""",
    "Insurance_Policy": """Insurance and Billing Policy

Purpose: To clarify how the hospital works with insurance providers and what patients can
expect regarding coverage, billing, and payment.

Accepted Providers: The hospital accepts major insurance providers including Blue Cross,
Medicare, Aetna, Cigna, and UnitedHealthcare, among others. Patients should confirm coverage
with the billing office prior to elective procedures.

Pre-Authorization: Certain procedures require pre-authorization from the insurance provider.
The billing office assists patients in submitting pre-authorization requests where applicable.

Co-Payments and Deductibles: Patients are responsible for any co-payments, deductibles, or
non-covered services as defined by their insurance plan. These are collected at discharge or
billed directly afterward.

Claims Processing: The hospital submits claims directly to the patient's insurance provider
on their behalf. Processing times vary by provider and typically range from two to six weeks.

Self-Pay Patients: Patients without insurance coverage are offered an itemized bill and may be
eligible for a self-pay discount or a payment plan, arranged through the billing office.

Disputed Charges: Patients may dispute a charge in writing within 30 days of receiving their
bill. The billing office will investigate and respond within 15 business days.
""",
    "Privacy_Policy": """Patient Privacy and Data Protection Policy

Purpose: To protect the confidentiality of patient health information in accordance with
applicable healthcare privacy regulations.

Scope of Protected Information: This policy covers all patient records, including diagnosis,
treatment history, billing details, and any identifying information, whether stored digitally
or on paper.

Access Control: Only authorized clinical and administrative staff directly involved in a
patient's care may access their records. Access is logged and subject to periodic audit.

Sharing with Third Parties: Patient information is not shared with employers, family members,
or other third parties without explicit written patient consent, except where required by law
(e.g., public health reporting, court order).

Data Security: Electronic health records are stored on encrypted, access-controlled systems.
Staff are prohibited from discussing patient information in public areas or over unsecured
channels.

Patient Rights to Their Own Data: Patients have the right to request a copy of their own
medical records and to request corrections to inaccurate information.

Breach Notification: In the event of a data breach affecting patient information, affected
patients will be notified in accordance with applicable law and hospital breach-response
procedures.
""",
    "Fire_Safety": """Fire Safety and Evacuation Protocol

Purpose: To protect patients, staff, and visitors in the event of a fire or related emergency.

Fire Alarm Response: Upon hearing the fire alarm, all staff must proceed to their designated
evacuation role (e.g., patient evacuation, corridor clearance, elevator lockout) as assigned
in the department fire plan.

Evacuation Priority: Ambulatory patients are evacuated first via the nearest marked stairwell,
followed by patients requiring wheelchair assistance, and finally bedridden or ICU patients
using evacuation sleds or beds, per staff training.

Elevators: Elevators must never be used during a fire evacuation. All movement is via marked
stairwells only.

Assembly Points: Each building has a designated outdoor assembly point, marked on evacuation
maps posted in every corridor and patient room. Department heads take roll call at the
assembly point.

Fire Extinguishers and Equipment: Fire extinguishers, hose reels, and fire doors are inspected
monthly. Staff are trained annually on extinguisher use for small, contained fires only.

Horizontal Evacuation: For fires contained to one area, patients may first be moved
horizontally to an adjacent fire compartment behind fire doors, rather than fully evacuating
the building, per the hospital's phased evacuation strategy.

Drills: Fire drills are conducted quarterly in every department, with results logged and
reviewed by the Safety Committee.
""",
    "Blood_Bank_SOP": """Blood Bank Standard Operating Procedure

Purpose: To ensure the safe collection, storage, testing, and distribution of blood products.

Donor Screening: All blood donors undergo health questionnaires and screening for transmissible
infections prior to donation, in accordance with national blood safety standards.

Storage Requirements: Red blood cells are stored at 2-6°C, platelets at 20-24°C with continuous
agitation, and plasma frozen at -18°C or colder. Storage units are monitored continuously with
automated temperature alarms.

Cross-Matching: Before any transfusion, the patient's blood type is confirmed and cross-matched
against the donor unit to rule out incompatibility. A second independent staff member verifies
the match before release.

Emergency Release: In life-threatening emergencies, O-negative uncrossmatched blood may be
released immediately upon a physician's verbal order, with formal paperwork completed
retrospectively.

Transfusion Monitoring: Patients are monitored closely for the first 15 minutes of any
transfusion and periodically thereafter for signs of adverse reaction, including fever, rash,
or breathing difficulty.

Traceability: Every unit of blood is tracked from donor to recipient, with records retained for
a minimum of ten years to support look-back investigations if needed.
""",
    "Emergency_Protocol": """Emergency Department Protocol

Purpose: To ensure rapid, prioritized, and safe care for patients arriving with urgent or
life-threatening conditions.

Triage System: All arriving patients are triaged within ten minutes using a five-level acuity
scale, from Level 1 (resuscitation, immediate) to Level 5 (non-urgent).

Resuscitation Cases: Level 1 patients (e.g., cardiac arrest, severe trauma) are taken directly
to a resuscitation bay, bypassing registration, with a full response team activated
immediately.

Code Team Activation: A hospital-wide "Code Blue" is called for any patient in cardiac or
respiratory arrest anywhere in the facility, activating the rapid response team.

Mass Casualty Response: In a mass casualty event, the Emergency Department activates its
disaster plan, which includes surge staffing, triage tents, and coordination with local
emergency services.

Communication with Family: A designated liaison keeps waiting family members updated during
active resuscitation efforts, without disclosing detailed clinical information prematurely.

Handover to Inpatient Teams: Once stabilized, patients are handed over to the appropriate
inpatient team (e.g., ICU, surgery, general ward) with a full verbal and written handover.
""",
    "Pharmacy_Policy": """Pharmacy Medication Management Policy

Purpose: To ensure safe prescribing, dispensing, and administration of medications throughout
the hospital.

Prescribing: Only licensed physicians, and nurse practitioners within their scope of practice,
may prescribe medications. All prescriptions are entered into the electronic system with
allergy and interaction checks performed automatically.

Dispensing: The pharmacy verifies each prescription against the patient's chart before
dispensing, checking for correct dose, route, and potential drug interactions.

High-Alert Medications: Medications such as insulin, opioids, and anticoagulants are classified
as high-alert and require independent double-checking by two staff members before
administration.

Controlled Substances: Controlled substances are stored in locked, access-logged cabinets.
Discrepancies in count are investigated immediately and reported to the Pharmacy Director.

Patient Counseling: Pharmacists counsel patients on new medications at discharge, including
purpose, dosage, timing, and potential side effects.

Adverse Drug Reactions: Any suspected adverse drug reaction is documented in the patient's
chart and reported to the Pharmacy and Therapeutics Committee for review.
""",
    "Patient_Rights": """Patient Rights and Responsibilities

Purpose: To inform patients of their rights and responsibilities while receiving care at the
hospital.

Right to Information: Patients have the right to receive clear information about their
diagnosis, treatment options, risks, and expected outcomes in a language they understand.

Right to Consent or Refuse: Patients have the right to give informed consent before any
procedure and to refuse treatment, understanding the possible consequences of that refusal.

Right to Privacy and Dignity: Patients have the right to privacy during examinations,
confidentiality of their medical information, and to be treated with dignity and respect
regardless of background.

Right to a Second Opinion: Patients may request a second medical opinion at any point in their
care without it affecting the quality of care they receive.

Right to Complain: Patients may file a complaint about their care through the Patient
Relations office without fear of reduced quality of care as a result.

Patient Responsibilities: Patients are asked to provide accurate health information, follow
agreed treatment plans, treat staff and other patients respectfully, and settle billing
obligations in a timely manner.
""",
    "Infection_Control": """Infection Prevention and Control Policy

Purpose: To minimize the risk of healthcare-associated infections for patients, staff, and
visitors.

Hand Hygiene: All staff must perform hand hygiene using alcohol-based sanitizer or soap and
water at the five critical moments: before patient contact, before an aseptic procedure, after
body fluid exposure risk, after patient contact, and after contact with the patient's
surroundings.

Personal Protective Equipment (PPE): Appropriate PPE (gloves, gowns, masks, eye protection) is
required based on the precaution level of the patient (standard, contact, droplet, or airborne).

Isolation Precautions: Patients with known or suspected transmissible infections are placed in
appropriate isolation rooms with clear signage indicating the required precautions for anyone
entering.

Environmental Cleaning: Patient rooms are terminally cleaned and disinfected after discharge,
with high-touch surfaces cleaned at least twice daily during a patient's stay.

Surveillance: The Infection Control team conducts ongoing surveillance for healthcare-associated
infections and reports trends to hospital leadership monthly.

Outbreak Response: Any cluster of infections is investigated immediately, with enhanced
precautions, cohorting, and staff education implemented as needed to contain spread.
""",
}


def _write_pdf(title: str, body: str, out_path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, title.replace("_", " "))
    pdf.ln(2)
    pdf.set_font("Helvetica", size=11)
    for paragraph in body.strip().split("\n\n"):
        pdf.multi_cell(0, 6, paragraph.strip())
        pdf.ln(3)
    pdf.output(str(out_path))


def generate_policy_documents_if_needed(force: bool = False) -> list[str]:
    """Generate all policy PDFs into settings.DOCS_DIR if they don't already exist."""
    generated = []
    for name, body in POLICY_DOCS.items():
        out_path = settings.DOCS_DIR / f"{name}.pdf"
        if out_path.exists() and not force:
            continue
        _write_pdf(name, body, out_path)
        generated.append(str(out_path))
        logger.info("Generated policy document: %s", out_path.name)
    if not generated:
        logger.info("All policy documents already exist; skipping generation.")
    return generated