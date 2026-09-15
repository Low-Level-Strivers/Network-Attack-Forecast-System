# ATTACK FORECAST SYSTEM — FINAL IMPLEMENTATION PROMPT

You are an expert full-stack AI/ML engineer and UI/UX engineer.

Update the existing **AI-Powered Predictive Cyber Defence / Attack Forecast System** according to the requirements below.

## IMPORTANT

- Work with the existing project structure and functionality.
- **Do not unnecessarily redesign or remove existing working features.**
- Preserve the existing architecture unless a change is required to implement the requirements.
- Do not create dummy cards, empty divisions, placeholder charts, or non-functional UI components.
- Every visible component must contain meaningful, system-generated information.
- Maintain consistent spacing, alignment, typography, responsiveness, and visual hierarchy across every page.
- Use a clean professional cybersecurity/SOC-style interface.
- Primary UI palette: **White**
- Secondary palette: **Black and Grey**
- Use additional colors only where they have a clear semantic purpose, such as risk levels, attack stages, feature attribution, progress, and alerts.

---

# 1. SEQUENTIAL K-STEP FORECASTING — CORE REQUIREMENT

The current system processes the uploaded CSV and displays the forecast result all at once.

### CHANGE THIS BEHAVIOUR.

The system must simulate network evolution **sequentially over time**.

Instead of:

```text
CSV
 ↓
Process Everything
 ↓
Display Final Forecast
```

implement:

```text
CSV
 ↓
Initial Network State S(t)
 ↓
Forecast K Future States
 ↓
Wait for configured time interval
 ↓
Move to next state
 ↓
Forecast the next K Future States
 ↓
Wait
 ↓
Continue sequentially
```

The dashboard must visually show the progression as a **live forecasting process**, not as a single static graph.

### Example

```text
Current State
     ↓
t+1 → t+2 → t+3 → t+4 → t+5
                         ↓
                  Advance interval
                         ↓
Next Current State
                         ↓
t+6 → t+7 → t+8 → t+9 → t+10
```

The system should continuously update the forecast as the simulated network time advances.

### Requirements

- Maintain a configurable forecast horizon **K**.
- Maintain a configurable simulation/update interval.
- Show the currently processed state clearly.
- Show which future states are being forecast.
- Animate/update the forecast timeline sequentially.
- Do not reveal the entire future trajectory instantly.
- Preserve chronological ordering.
- The forecast must be derived from the actual uploaded CSV states.

---

# 2. CSV UPLOAD PAGE

The current upload page is mostly empty before a file is uploaded.

Replace the empty state with a useful professional interface.

### Before Upload

Display:

**Upload Network Traffic**

> Upload a CIC-IDS2017-compatible CSV file to reconstruct network states and forecast future attack progression.

Include:

- CSV upload area
- Supported format
- Short explanation of the processing pipeline
- Expected input information
- Processing stages

Example visual pipeline:

```text
CSV Upload
   ↓
Parse Traffic
   ↓
Build Network States
   ↓
Learn/Load Forecast Model
   ↓
Sequential Future Forecast
```

Do not overload the page with unnecessary information.

---

# 3. LIVE CSV PROCESSING & STATE CONSTRUCTION

After CSV upload, processing must be visually represented.

Do not simply show:

> "Processing..."

Instead show actual processing stages.

### Processing Pipeline

```text
1. CSV Validation
       ↓
2. Timestamp Parsing
       ↓
3. Data Cleaning
       ↓
4. Feature Extraction
       ↓
5. Time-Window Aggregation
       ↓
6. Network State Construction
       ↓
7. State Vector Generation
       ↓
8. Sequential Forecast Initialization
```

Display the progress dynamically.

For example:

```text
CSV Parsing                  ✓
Data Cleaning                ✓
Feature Extraction           ✓
State Construction            72%
Forecast Initialization       Waiting
```

The progress should update based on actual processing rather than fake animation.

The uploaded CSV's processing status must remain visible alongside the forecasting process.

---

# 4. NETWORK STATE STORAGE

The system must maintain a complete record of the states generated from the uploaded CSV.

For every time window, store:

```text
Timestamp
State ID
State Vector
State Vector Attributes
Risk Score
Predicted Stage
Important Features
Processing Status
```

Example:

```text
State S001
Timestamp: 08:54

Flow Count: ...
Port Diversity: ...
Packet Rate: ...
Byte Rate: ...
SYN Count: ...
ACK Count: ...
IAT Mean: ...
...
```

Do not store only the final result.

**Every generated network state must be retained.**

The system should be able to retrieve these states later for visualization, analysis, and historical logs.

---

# 5. LIVE STATE VISUALIZATION

While the CSV is being processed, the dashboard should progressively display the generated states.

Example:

```text
08:54  →  S001  ✓
08:55  →  S002  ✓
08:56  →  S003  ✓
08:57  →  S004  Processing
08:58  →  S005  Pending
```

The user should be able to see the network evolving through time.

When a state becomes active, display its important state-vector attributes.

---

# 6. MITRE ATT&CK TACTICAL PROGRESSION PAGE

The existing MITRE ATT&CK page contains an empty division.

Replace it with meaningful system-generated content.

Display the predicted tactical progression as a timeline.

Example:

```text
Current
   ↓
Reconnaissance
   ↓
Initial Access
   ↓
Execution
   ↓
Persistence
```

For every predicted stage, show where applicable:

- Tactical stage
- Prediction confidence
- Associated behaviour
- Relevant MITRE ATT&CK technique
- Corresponding forecast time/state

The visualization must be based on the system's prediction rather than hard-coded dummy values.

Clearly distinguish:

**Observed/current behaviour**

from

**Predicted future behaviour.**

---

# 7. EXPLAINABILITY / XAI PAGE

The current XAI page contains an empty division.

Replace it with a complete explainability interface.

The page should answer:

> **"Why is the system predicting increasing future attack risk?"**

Display:

### Feature Attribution Ranking

Show the most influential features responsible for the prediction.

Example:

```text
Port Diversity       ███████████
SYN Flag Count       █████████
Flow IAT Mean        ███████
Packet Rate          █████
Flow Duration        ███
```

### IMPORTANT

The feature attribution bars must be:

**HORIZONTAL**

not vertical.

Use appropriate semantic colors to distinguish:

- Features increasing risk
- Features decreasing risk
- Neutral/low contribution

The colors should remain consistent throughout the application.

Do not use random decorative colors.

---

# 8. FORECAST EXPLAINABILITY

XAI should support the future trajectory, not only the current state.

For each future forecast step, where possible, display:

```text
t+1
Risk: 32%
Main drivers:
• Port Diversity
• SYN Activity

t+2
Risk: 47%
Main drivers:
• SYN Activity
• Flow IAT

t+3
Risk: 68%
Main drivers:
• Port Diversity
• Packet Rate
```

This should make the prediction understandable to a security analyst.

---

# 9. FORECAST LOGGING SYSTEM

Create a persistent logging mechanism for every uploaded CSV processing operation.

For each upload, store:

```text
Upload ID
File Name
Upload Time
Processing Start Time
Processing End Time
Number of Rows
Number of Generated States
Processing Status
Forecast Configuration
Forecast Results
```

Additionally store the complete state history:

```text
State ID
Timestamp
State Vector
State Attributes
Risk
Predicted Stage
Important Features
Forecast Results
```

The system must not lose this information after the current dashboard session.

---

# 10. OPERATION HISTORY PAGE

Create a dedicated page for previous processing operations.

Display all previously processed CSV operations.

Example:

```text
OPERATIONS

CSV File              States     Risk       Status
──────────────────────────────────────────────────
Tuesday.csv           421        High       Completed
Wednesday.csv         518        Medium     Completed
Thursday.csv          392        Low        Completed
```

Selecting an operation should open its historical analysis.

---

# 11. HISTORICAL STATE EXPLORER

For each previous operation, allow the user to inspect the generated states.

Example:

```text
Operation: Tuesday.csv

08:54   S001   Low Risk
08:55   S002   Low Risk
08:56   S003   Medium Risk
08:57   S004   Medium Risk
08:58   S005   High Risk
```

Selecting a state should display:

- Timestamp
- State vector attributes
- Risk score
- Predicted attack stage
- Top contributing features
- Forecast associated with that state

This page should visually communicate **how the network evolved over time**.

---

# 12. MAIN DASHBOARD

The main dashboard should combine the most important live information.

### Recommended layout

```text
┌─────────────────────────────────────────────┐
│ Predictive Cyber Defence      System Status │
├───────────┬────────────┬────────────────────┤
│ Current   │ Future     │ Predicted Attack   │
│ Risk      │ Risk       │ Stage              │
├───────────┴────────────┴────────────────────┤
│                                             │
│ Sequential Future Risk Timeline             │
│                                             │
├──────────────────────┬──────────────────────┤
│ Current Network State │ Forecast Trajectory │
│                      │                      │
├──────────────────────┴──────────────────────┤
│ CSV Processing / State Construction         │
├─────────────────────────────────────────────┤
│ Early Warning                               │
└─────────────────────────────────────────────┘
```

The dashboard must update as the sequential forecasting process advances.

---

# 13. COLOR & UI SYSTEM

Use a consistent design system.

### Primary

**White**

### Secondary

**Black / Dark Grey**

### Supporting

**Light Grey / Medium Grey**

### Semantic Colors

Use restrained semantic colors only for:

- Low risk
- Medium risk
- High risk
- Successful processing
- Warning
- Prediction/forecast
- Positive/negative feature contribution

Do not make every card a different color.

The interface should look like a **professional SOC/security analytics platform**, not a gaming dashboard.

---

# 14. RESPONSIVE & STRUCTURAL QUALITY

Verify every page for:

- No blank divisions
- No overlapping components
- No broken alignment
- No excessive whitespace
- No clipped text
- No inconsistent card sizes
- No unnecessary scrolling
- No dummy data
- No broken charts
- No missing states
- No duplicated components
- Proper responsive behaviour

All pages should use a consistent:

**Header → Navigation → Content → Footer/Status**

structure where appropriate.

---

# 15. DATA INTEGRITY

The system must preserve the chronological relationship between:

```text
CSV Timestamp
      ↓
Network State
      ↓
State Vector
      ↓
Forecast
      ↓
Risk
      ↓
Attack Stage
      ↓
XAI Explanation
      ↓
Log
```

Every forecast displayed on the dashboard must be traceable back to the corresponding network state.

Do not generate arbitrary values merely to populate the UI.

---

# 16. FINAL END-TO-END USER FLOW

The final application should behave like this:

```text
USER OPENS SYSTEM
        ↓
UPLOAD CSV
        ↓
SHOW FILE INFORMATION
        ↓
START PROCESSING
        ↓
LIVE PARSING PROGRESS
        ↓
LIVE STATE CONSTRUCTION
        ↓
STATE S001 CREATED
        ↓
FORECAST K FUTURE STATES
        ↓
DISPLAY CURRENT + FUTURE FORECAST
        ↓
WAIT FOR SIMULATION INTERVAL
        ↓
MOVE TO NEXT STATE
        ↓
FORECAST NEXT K STATES
        ↓
UPDATE RISK TIMELINE
        ↓
UPDATE ATTACK TRAJECTORY
        ↓
UPDATE MITRE STAGE
        ↓
UPDATE XAI FEATURES
        ↓
STORE STATE + FORECAST LOG
        ↓
CONTINUE UNTIL DATASET IS COMPLETED
        ↓
SAVE COMPLETE OPERATION
        ↓
USER CAN OPEN HISTORICAL LOG
        ↓
INSPECT EVERY STATE AND FORECAST
```

---

# 17. FINAL VALIDATION BEFORE COMPLETION

After implementing all changes, perform a complete verification.

### Functional verification

Confirm that:

- CSV upload works.
- CSV parsing works.
- State construction works.
- All generated states are stored.
- Sequential forecasting works.
- K-step forecasting works.
- Forecast advances according to the configured interval.
- MITRE progression is populated.
- XAI page is populated.
- Feature attribution is horizontal.
- Historical operations are stored.
- Historical states can be viewed.
- Dashboard updates dynamically.

### UI verification

Confirm that:

- No blank content divisions remain.
- No dummy components remain.
- No alignment errors exist.
- No overflow exists.
- No broken charts exist.
- Colors are consistent.
- Headers are consistent.
- Pages are visually coherent.
- The complete application is responsive.

### MOST IMPORTANT VALIDATION

Verify that the application demonstrates the actual project concept:

> **The system should not simply process a CSV and display one final prediction. It must reconstruct the network's chronological states, forecast future states sequentially, visualize the evolving risk/attack trajectory, explain the predictions, and preserve the complete state and forecast history.**

The final result should feel like a **functional Predictive Cyber Defence prototype**, not a collection of static dashboard screens.