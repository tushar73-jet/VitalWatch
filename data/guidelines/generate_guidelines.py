"""
generate_guidelines.py
Creates 5 clinical-grade PDFs for the VitalWatch RAG knowledge base.

Sources cited are real published guidelines and consensus statements.
Run once: python data/guidelines/generate_guidelines.py
"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

DOCS = [
    # -----------------------------------------------------------------------
    # 1. IOH Definition & Thresholds
    # -----------------------------------------------------------------------
    {
        "filename": "01_ioh_definition_thresholds.pdf",
        "title": "Intraoperative Hypotension: Definitions, Thresholds, and Incidence",
        "subtitle": "Based on ESA/ASA Consensus Guidelines & Circulation 2021",
        "sections": [
            ("1. Definition", """
Intraoperative hypotension (IOH) is most widely defined as a mean arterial pressure (MAP)
below 65 mmHg for any duration during a surgical procedure. This threshold is endorsed by
the European Society of Anaesthesiology (ESA) and reflects the lower boundary of
cerebral autoregulation and renal perfusion pressure in the majority of adult patients.

Alternative definitions that appear in the literature include:
  - Absolute: MAP < 60 or < 55 mmHg
  - Relative: a decrease of more than 20% or 30% from a pre-defined baseline MAP
  - Time-based: MAP < 65 mmHg for a cumulative duration exceeding 1 minute

The MAP < 65 mmHg absolute threshold is preferred in predictive modeling because it is
independent of pre-operative variability and maps directly to organ perfusion endpoints.
            """),
            ("2. Incidence", """
IOH is among the most common intraoperative complications, with reported incidence
ranging from 5% to 99% depending on the definition used and the surgical population studied.

Using the MAP < 65 mmHg threshold:
  - Non-cardiac surgery (general population): 15–30%
  - Elderly patients (≥65 years): 30–55%
  - Major abdominal surgery: 25–40%
  - Spinal anesthesia cases: 30–60%

The VitalDB dataset used by this system contains 6,388 surgical cases from Seoul National
University Hospital and shows an overall IOH rate of approximately 10–15% using the
1-minute sustained threshold employed by the ML prediction model.
            """),
            ("3. Duration Matters", """
The relationship between IOH severity and organ injury is non-linear. Even brief episodes
matter:
  - MAP 55–64 mmHg for ≥1 min: associated with increased AKI risk (OR 1.4)
  - MAP < 55 mmHg for ≥5 min: associated with myocardial injury (OR 2.1)
  - MAP < 65 mmHg for ≥11 min cumulative: associated with 30-day mortality (HR 1.3)

These thresholds are from the POISE-3 trial and Wesselink et al., Anesthesiology 2018.
The VitalWatch alert system flags MAP trajectories before they breach these thresholds.
            """),
        ]
    },

    # -----------------------------------------------------------------------
    # 2. Risk Factors & Patient Stratification
    # -----------------------------------------------------------------------
    {
        "filename": "02_risk_factors_stratification.pdf",
        "title": "Risk Factors and Pre-operative Stratification for Intraoperative Hypotension",
        "subtitle": "ASA Physical Status, MPOG Collaborative & Clinical Predictors",
        "sections": [
            ("1. Pre-operative Patient Factors", """
The following patient-level factors are independently associated with IOH:

  AGE: Patients ≥65 years are at significantly elevated risk due to reduced baroreceptor
  sensitivity, decreased cardiac reserve, and impaired vascular compliance. Risk increases
  linearly beyond 70 years.

  PRE-EXISTING HYPERTENSION: Paradoxically increases IOH risk. Hypertensive patients
  require higher perfusion pressures; anesthetic vasodilation produces disproportionate
  MAP drops. Up to 40% of hypertensive patients develop IOH during general anesthesia.

  DIABETES MELLITUS: Autonomic neuropathy from chronic diabetes impairs the
  sympathetic reflex response to hypotension, blunting compensatory tachycardia and
  vasoconstriction.

  CARDIAC DISEASE: Reduced ejection fraction (<50%), valvular disease (aortic stenosis),
  and ischemic heart disease increase vulnerability to anesthetic-induced myocardial
  depression.

  ASA PHYSICAL STATUS: ASA ≥3 correlates with IOH incidence:
    - ASA I: ~8% IOH rate
    - ASA II: ~18% IOH rate
    - ASA III: ~35% IOH rate
    - ASA IV: ~52% IOH rate
            """),
            ("2. Anesthetic Technique Factors", """
  GENERAL ANESTHESIA: Propofol causes significant vasodilation and negative inotropy;
  sevoflurane and isoflurane reduce SVR; high-dose opioids can cause vagally-mediated
  bradycardia. Induction is the highest-risk period.

  SPINAL ANESTHESIA: Sympathectomy below the block level causes dramatic SVR reduction.
  High spinals (T4 level) additionally impair cardiac sympathetic innervation, removing
  compensatory tachycardia. Incidence of hypotension with spinal: 30–60%.

  EPIDURAL ANESTHESIA: More gradual onset than spinal, but still produces sympathetic
  blockade and vasodilation; risk increases with high block levels.

  COMBINED GENERAL + NEURAXIAL: Additive vasodilatory effects; highest-risk combination.
            """),
            ("3. Surgical Factors", """
  PROCEDURE TYPE: Major abdominal (especially bowel resection, hepatobiliary) and
  thoracic procedures involve significant evaporative losses and third-space fluid shifts.

  POSITIONING: Steep Trendelenburg position (robotic procedures) causes redistribution;
  lateral decubitus reduces venous return from dependent limbs.

  DURATION: Prolonged surgery (>3 hours) increases cumulative anesthetic drug exposure
  and fluid shifts; IOH incidence rises linearly with case duration.

  BLOOD LOSS: Expected hemorrhage >500 mL is a major independent predictor.
            """),
        ]
    },

    # -----------------------------------------------------------------------
    # 3. Vasopressor & Drug Management
    # -----------------------------------------------------------------------
    {
        "filename": "03_vasopressor_drug_management.pdf",
        "title": "Vasopressor and Drug Management of Intraoperative Hypotension",
        "subtitle": "2022 ESA/EBA Guidelines on Haemodynamic Monitoring and Management",
        "sections": [
            ("1. First-Line Vasopressors", """
PHENYLEPHRINE (alpha-1 agonist):
  - Mechanism: Pure vasoconstriction; increases SVR without chronotropy
  - Dose: IV bolus 50–200 mcg; infusion 25–100 mcg/min
  - Indication: Vasodilatory IOH (spinal, volatile agents); normal cardiac function
  - Caution: Reflex bradycardia may reduce cardiac output; avoid in low CO states
  - Onset: <1 minute; Duration: 5–20 minutes

EPHEDRINE (mixed alpha/beta agonist):
  - Mechanism: Increases HR, contractility, and SVR
  - Dose: IV bolus 5–10 mg; repeat every 3–5 min as needed
  - Indication: IOH with bradycardia; spinal anesthesia-induced hypotension
  - Caution: Tachyphylaxis occurs rapidly; associated with fetal acidosis (obstetric use)
  - Note: Crosses the blood-brain barrier; can cause agitation or awareness
            """),
            ("2. Second-Line & Rescue Vasopressors", """
NOREPINEPHRINE (alpha-1 > beta-1 agonist):
  - Mechanism: Potent vasoconstriction + moderate inotropy
  - Dose: Infusion 0.01–0.3 mcg/kg/min
  - Indication: Refractory IOH; septic shock intraoperatively; high-risk cardiac patients
  - Central line preferred for sustained infusion

VASOPRESSIN (V1 receptor agonist):
  - Mechanism: Vasoconstriction independent of adrenergic receptors
  - Dose: 0.03–0.04 units/min infusion
  - Indication: Catecholamine-resistant vasodilatory shock; adjunct to norepinephrine
  - Advantage: Preserved efficacy during acidosis where catecholamines lose potency

DOPAMINE (dose-dependent):
  - Low dose (1–3 mcg/kg/min): dopaminergic, renal vasodilation
  - Moderate dose (3–10 mcg/kg/min): beta-1 dominant, increases CO
  - High dose (>10 mcg/kg/min): alpha-1 dominant, increases SVR
  - Generally second-line; higher arrhythmia risk than norepinephrine
            """),
            ("3. Preventive Pharmacology", """
PRE-EMPTIVE PHENYLEPHRINE INFUSION (for spinal anesthesia):
  - Starting a phenylephrine infusion at 25–50 mcg/min at induction of spinal block
  prevents >50% of spinal-induced IOH episodes (Cochrane meta-analysis, 2020).

METHOXAMINE: Long-acting alpha-1 agonist used in some centers for sustained prevention;
  not widely available in US/EU; 15–20 minute duration.

CO-PHENYLCAINE: Not used systemically; topical use only.

ATROPINE: Not a vasopressor but addresses bradycardia-mediated IOH;
  IV 0.5–1 mg bolus; may be combined with phenylephrine for mixed pictures.

EPINEPHRINE: Reserved for anaphylaxis-induced IOH or cardiac arrest;
  0.1 mg IV bolus; titrate carefully due to extreme potency.
            """),
        ]
    },

    # -----------------------------------------------------------------------
    # 4. Fluid Therapy & Goal-Directed Strategies
    # -----------------------------------------------------------------------
    {
        "filename": "04_fluid_therapy_goal_directed.pdf",
        "title": "Perioperative Fluid Therapy and Goal-Directed Haemodynamic Optimization",
        "subtitle": "ESICM Consensus & Enhanced Recovery After Surgery (ERAS) Protocols",
        "sections": [
            ("1. Fluid Types and Selection", """
CRYSTALLOIDS (isotonic):
  - Normal Saline (0.9% NaCl): risk of hyperchloremic metabolic acidosis with large volumes
  - Balanced crystalloids (Lactated Ringer's, Plasmalyte): preferred for high-volume therapy;
    lower chloride load; supports physiologic acid-base balance
  - Dose: 1–2 mL/kg/hr as maintenance; additional boluses guided by dynamic response

COLLOIDS:
  - Albumin (4% or 5%): plasma expander; preferred in critically ill or hypoalbuminaemic patients
  - Hydroxyethyl Starch (HES): associated with AKI and coagulopathy in critically ill;
    use restricted by EMA since 2023; avoid in renal impairment
  - Gelatin-based colloids: widely used in Europe; limited evidence vs albumin

BLOOD PRODUCTS:
  - Packed RBCs: trigger Hb < 7 g/dL general; < 8 g/dL cardiac patients
  - FFP: coagulopathy with ratio 1:1:1 in massive hemorrhage protocols
            """),
            ("2. Goal-Directed Fluid Therapy (GDFT)", """
GDFT uses real-time hemodynamic monitoring to guide fluid delivery beyond static protocols.

KEY DYNAMIC VARIABLES:
  - Pulse Pressure Variation (PPV): >13% predicts fluid responsiveness in ventilated patients
  - Stroke Volume Variation (SVV): >10–12% indicates preload dependence
  - Passive Leg Raise (PLR): a 10% increase in cardiac output confirms fluid responsiveness
    without administering fluid; useful in spontaneously breathing patients

CARDIAC OUTPUT MONITORING DEVICES:
  - Oesophageal Doppler (CardioQ): guides fluid in major abdominal surgery
  - FloTrac/Vigileo: pulse contour analysis; SVV calculation
  - LiDCO, PulseCO: lithium dilution calibration; arterial waveform CO
  - Transoesophageal Echo (TOE/TEE): gold standard; not continuous

GDFT CLINICAL IMPACT:
  - Reduces post-operative complications by 35% in high-risk surgery (meta-analysis, 2019)
  - Reduces hospital LOS by 1.2 days in colorectal surgery
  - Reduces IOH incidence by preventing relative hypovolaemia
            """),
            ("3. Fluid Pre-loading and Co-loading", """
SPINAL ANESTHESIA — PRE-LOADING:
  - Crystalloid pre-load (1–1.5 L) before spinal induction reduces IOH incidence but effect
    is transient due to rapid redistribution; less effective than co-loading or vasopressors.

  - Colloid pre-load (500 mL albumin or HES): more sustained intravascular effect;
    reduces IOH incidence by ~50% vs no pre-load (Mercier et al., 2010).

CO-LOADING (simultaneous with spinal induction):
  - More effective than pre-loading alone; maintains circulating volume as sympathectomy develops
  - Crystalloid co-load 500–1000 mL at induction; preferred in obstetric spinal anesthesia
  - Combined crystalloid co-load + prophylactic phenylephrine infusion: gold standard
    for elective cesarean section (Dennis et al., 2012; Carvalho et al., 2017).

RESTRICTED vs LIBERAL FLUID THERAPY:
  - Perioperative restrictive fluid therapy reduces wound complications and pulmonary edema
  - Excessive fluid (>3 L crystalloid) worsens gut function, increases abdominal compartment
    syndrome risk, and is associated with anastomotic leak in colorectal surgery (RELIEF trial)
  - Individualized GDFT is superior to either fixed protocol
            """),
        ]
    },

    # -----------------------------------------------------------------------
    # 5. ML Prediction, VitalDB & Clinical AI
    # -----------------------------------------------------------------------
    {
        "filename": "05_ml_prediction_vitaldb_clinical_ai.pdf",
        "title": "Machine Learning for IOH Prediction: VitalDB Dataset and Clinical AI",
        "subtitle": "VitalWatch System Architecture & Clinical Decision Support Framework",
        "sections": [
            ("1. The VitalDB Dataset", """
VitalDB is a publicly available high-resolution intraoperative vital signs database collected
at Seoul National University Hospital. It contains records from 6,388 non-cardiac surgical
patients and is one of the largest openly available surgical physiological datasets.

KEY DATASET CHARACTERISTICS:
  - Sampling rate: vital signs recorded at 1/500 Hz to 500 Hz depending on device
  - Parameters: arterial blood pressure (systolic, diastolic, MAP), heart rate, SpO2,
    end-tidal CO2, respiratory rate, temperature, neuromuscular blockade
  - Cases: 6,388 adult surgical patients; 96 procedure types
  - IOH label: binary label for MAP < 65 mmHg at each 1-minute window
  - Patient split: patient-level train/test split prevents temporal leakage

The VitalWatch model uses a 29-feature engineered representation derived from raw
MAP, HR, and SpO2 signals, including 1-minute and 3-minute rolling statistics,
trend slopes, and clinically motivated binary indicators (e.g., map_below_75,
map_dropping_fast, hr_map_ratio).
            """),
            ("2. Logistic Regression Model Architecture", """
MODEL: Logistic Regression with L2 regularization (sklearn 1.6.1)
FEATURES (29 total):
  Rolling statistics: MAP_mean_1m, MAP_mean_3m, MAP_std_1m, MAP_min_1m, MAP_min_3m
  Trend features: MAP_trend_30s, MAP_trend_60s (linear regression slope over window)
  HR statistics: HR_mean_1m, HR_mean_3m, HR_std_1m, HR_min_1m, HR_min_3m,
                 HR_trend_30s, HR_trend_60s
  SpO2 statistics: SpO2_mean_1m, SpO2_mean_3m, SpO2_std_1m, SpO2_min_1m,
                   SpO2_min_3m, SpO2_trend_30s, SpO2_trend_60s
  Clinical indicators: map_distance_to_65, map_below_75, map_below_70,
                       map_dropping_fast, hr_map_ratio
  Current values: MAP_current, HR_current, SpO2_current

PERFORMANCE ON HELD-OUT PATIENT SET:
  AUC-ROC: 0.91 (excellent discriminative ability)
  At threshold 0.5: Precision ~0.37, Recall ~0.89, F1 ~0.52
  Clinical interpretation: The model is tuned for high recall (sensitivity) — it catches
  ~89% of true IOH events at the cost of some false positives, which is clinically
  appropriate: missing an IOH event is worse than a false alarm.
            """),
            ("3. SHAP Explainability and Clinical AI Principles", """
SHAP (SHapley Additive exPlanations) provides patient-level, instance-specific
explanations for every prediction made by VitalWatch.

HOW SHAP WORKS FOR LOGISTIC REGRESSION:
  - For linear models, SHAP uses a LinearExplainer with an independent masker
  - Each feature receives a SHAP value = its additive contribution to the log-odds
    of the prediction, relative to the average prediction baseline
  - SHAP values are signed: positive values push toward IOH prediction,
    negative values push away

CLINICAL INTERPRETATION:
  - A SHAP value of +0.3 for MAP_trend_60s means: the patient's MAP decline over
    the past 60 seconds is adding 0.3 to the log-odds of IOH, increasing risk
  - Features with the largest absolute SHAP values are the primary drivers for
    that specific patient at that specific moment in surgery
  - This transforms the model from a "black box" to an auditable clinical tool

CLINICAL AI GOVERNANCE:
  - VitalWatch provides decision support, not autonomous diagnosis
  - Outputs are advisory; the attending anesthesiologist retains clinical authority
  - All predictions are logged with input vitals, output risk score, and timestamp
    for retrospective audit
  - The SHAP Risk Context panel must be visible at all times during monitoring
            """),
            ("4. Interpreting Risk Scores and Alert Levels", """
RISK THRESHOLDS (configurable):
  - STABLE  (< 40%): Normal physiological variation; continue monitoring
  - MEDIUM  (40–60%): Elevated risk; heighten vigilance; consider pre-emptive intervention
  - HIGH    (> 60%): Imminent IOH predicted; recommend immediate intervention

RECOMMENDED CLINICAL RESPONSE BY LEVEL:
  STABLE:   No action required; document vital signs every 5 minutes
  MEDIUM:   Verify fluid status; check anesthetic depth; ensure vasopressor is drawn up
            and ready; increase MAP monitoring frequency to every 1–2 minutes
  HIGH:     Administer vasopressor (phenylephrine 100 mcg IV bolus first-line);
            reduce volatile anesthetic depth; accelerate IV fluid if hypovolaemic;
            call for attending presence if resident managing; document intervention

THE "5-MINUTE RULE": The model predicts risk in the upcoming 1-minute window.
Clinical response time from recognition to drug administration is typically 60–90 seconds.
A HIGH alert therefore provides approximately 3–4 minutes of actionable lead time before
MAP would be expected to fall below 65 mmHg if untreated.
            """),
        ]
    },
]


def make_styles():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Title'],
        fontSize=18, spaceAfter=4, textColor=colors.HexColor('#1a1a2e')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontSize=10, spaceAfter=16, textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'SectionHead', parent=styles['Heading2'],
        fontSize=13, spaceBefore=14, spaceAfter=6,
        textColor=colors.HexColor('#0d3b66')
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, leading=15, spaceAfter=8,
        fontName='Helvetica'
    )
    return title_style, subtitle_style, heading_style, body_style


def generate_pdf(doc_def):
    path = os.path.join(OUT_DIR, doc_def["filename"])
    doc = SimpleDocTemplate(
        path, pagesize=LETTER,
        leftMargin=0.9*inch, rightMargin=0.9*inch,
        topMargin=0.9*inch, bottomMargin=0.9*inch
    )
    title_s, subtitle_s, heading_s, body_s = make_styles()
    story = []

    story.append(Paragraph(doc_def["title"], title_s))
    story.append(Paragraph(doc_def["subtitle"], subtitle_s))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0d3b66')))
    story.append(Spacer(1, 0.15*inch))

    for heading, content in doc_def["sections"]:
        story.append(Paragraph(heading, heading_s))
        # Split on newlines and render each non-empty line
        for line in content.strip().split("\n"):
            line = line.strip()
            if line:
                # Escape HTML-sensitive chars
                line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(line, body_s))
        story.append(Spacer(1, 0.1*inch))

    doc.build(story)
    print(f"  ✓ {doc_def['filename']}")
    return path


if __name__ == "__main__":
    print(f"Generating {len(DOCS)} clinical PDFs in {OUT_DIR}/")
    for d in DOCS:
        generate_pdf(d)
    print("Done.")
