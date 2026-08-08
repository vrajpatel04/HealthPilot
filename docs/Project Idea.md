# 🩺 HealthPilot AI
## Behavioral AI Wellness Recommendation Agent

> **"It doesn't just know what you click. It learns what you need next."**

HealthPilot AI is an **agentic AI wellness marketplace** that learns from how users browse, search, interact, and engage with wellness content.

It combines:

- Behavioral intelligence
- RAG
- Vector search
- Long-term memory
- Agentic AI
- Personalized persuasion
- Optional lifestyle signals
- Optional blood report analysis
- Presidio PII/PHI de-identification
- NeMo Guardrails safety policies

to recommend the most relevant wellness courses, programs, guides, and products — without exposing personal identifiers to external LLMs.

The recommendations continuously evolve as the user's behavior changes.

---

# 1. 🚨 Problem

Traditional recommendation systems are mostly based on:

- "Users who bought this also bought..."
- Popular products
- Categories
- Basic search keywords
- Static user preferences

They don't understand **why a user is interested in something**.

For example, a user:

- Searches for "how to sleep better"
- Views 3 sleep courses
- Reads a sleep article
- Spends 8 minutes on one course
- Returns to the same course later
- Searches for "night routine"
- Ignores generic fitness recommendations

A traditional recommendation engine may simply show:

> Popular Health Courses

HealthPilot instead understands:

> "This user has developed strong intent around improving sleep and is showing high engagement with structured sleep programs."

It then retrieves the most relevant products and generates a personalized recommendation.

---

# 2. 💡 Solution

HealthPilot AI continuously observes user behavior and builds a dynamic understanding of the user's interests.

It combines:

```text
User Behavior
      +
Lifestyle Signals
      +
Long-Term Memory
      +
Product Catalog
      +
RAG Knowledge
      +
Optional Health Report
      ↓
Agentic AI
      ↓
Personalized Recommendation
      +
Persuasive Explanation
```

Instead of simply recommending:

> Sleep Better in 21 Days

the system explains:

> **You've been exploring sleep improvement content throughout the day, and you've returned to this program twice. Since you seem to prefer structured, gradual changes, this 21-day program looks like the best next step for you.**

---

# 3. 🎯 Core Objectives

HealthPilot should:

- Observe user behavior
- Understand user intent
- Build long-term behavioral memory
- Retrieve relevant products using semantic search
- Ground recommendations using RAG
- Generate personalized persuasive messages
- Continuously update recommendations
- Learn from user feedback
- Minimize unnecessary AI calls
- Cache recommendations when appropriate
- Proactively deliver recommendations
- Keep product data synchronized between SQL and vector storage
- De-identify free text before any external LLM call
- Enforce wellness-only guardrails on user-facing AI output
- Pass biomarkers to LLMs only as structured fields, never as raw report text

---

# 4. 👤 Example User Journey

## Step 1 — User Signs Up

```text
Name: Rahul
Email: rahul@example.com
Goal: Improve lifestyle
```

---

## Step 2 — User Explores the Marketplace

HealthPilot contains:

### Courses

```text
Sleep Better in 21 Days
Beginner Walking Program
Healthy Meal Planning
Stress Management
Morning Routine Mastery
```

### Programs

```text
30-Day Wellness Challenge
Office Worker Wellness
Beginner Fitness Program
Sleep Improvement Program
```

### Digital Products

```text
7-Day Meal Plan
Morning Routine Guide
Sleep Tracker
Habit Tracker
```

---

# 5. 📊 Behavioral Tracking

Rahul starts browsing.

The frontend tracks meaningful events:

```text
10:02
Viewed "Sleep Better in 21 Days"

10:04
Read 72% of description

10:06
Searched "sleep improvement"

10:08
Viewed "Morning Routine Guide"

10:12
Viewed "Stress Management"

10:15
Searched "sleep"

10:20
Returned to "Sleep Better in 21 Days"
```

The system does **not** call the LLM after every event.

Instead, events are collected and analyzed efficiently.

---

# 6. ⚡ Efficient Event Tracking

Frontend events are:

```text
User Action
     ↓
Client-side Event Queue
     ↓
Batching / Throttling
     ↓
POST /events/batch
     ↓
FastAPI
     ↓
PostgreSQL
```

High-frequency events such as scrolling are throttled.

Example:

```text
scroll
scroll
scroll
scroll
scroll

      ↓

throttle

      ↓

meaningful scroll event
```

This ensures tracking does not slow down the application.

---

# 7. 🧠 Behavioral Analysis

The Behavior Agent periodically analyzes accumulated events.

Instead of processing:

```text
10 individual events
```

it creates a behavioral summary:

```json
{
  "primary_interest": "sleep improvement",
  "secondary_interest": "stress management",
  "search_frequency": 2,
  "high_intent_product": "Sleep Better in 21 Days",
  "engagement": "high",
  "return_visit": true
}
```

The AI now understands **intent**, not just clicks.

---

# 8. 🧠 Long-Term User Memory

HealthPilot maintains persistent behavioral memory.

Example:

```text
USER MEMORY

Primary Interest:
Sleep Improvement

Secondary Interest:
Stress Management

Preferred Content:
Structured Programs

Behavior:
Frequently revisits sleep content

Engagement:
High

Previous Successful Recommendation:
Sleep Routine Guide
```

Over time, this profile changes automatically.

---

# 9. 🧬 Optional Lifestyle Signals

HealthPilot can also collect lifestyle information such as:

```text
Sleep
Steps
Water
Screen Time
Food
Mood
```

Example:

```text
Average Sleep: 5.3 hours
Average Steps: 2,200
Water: 1.4L/day
Screen Time: 8 hours/day
```

These signals provide additional context for recommendation generation.

---

# 10. 🩸 Optional Blood Report Personalization

Users can optionally upload:

- Blood report PDF
- Blood report image

The system extracts relevant structured information.

Example:

```text
HbA1c: 6.2
Vitamin D: 14
LDL: 162
HDL: 38
Triglycerides: 230
```

The Blood Report Agent converts the document into structured data:

```json
{
  "biomarkers": {
    "hba1c": 6.2,
    "vitamin_d": 14,
    "ldl": 162,
    "hdl": 38,
    "triglycerides": 230
  }
}
```

This information becomes an **optional personalization signal**.

- Biomarkers are stored as **structured fields** in PostgreSQL
- Raw report OCR text is **not** sent to Mesh API
- Any user-facing summary from report analysis runs through the **privacy pipeline** (Presidio → NeMo → LLM → NeMo → Presidio)

It is not used to diagnose diseases or prescribe treatment.

---

# 11. 📚 RAG Knowledge Base

HealthPilot maintains a trusted knowledge base containing wellness information.

Examples:

```text
Sleep Guidelines
Nutrition Guidelines
Physical Activity Guidelines
Hydration Information
Stress Management
Healthy Lifestyle Guides
Wellness Articles
```

Documents are processed through:

```text
Documents
    ↓
Chunking
    ↓
Embeddings
    ↓
Qdrant
```

When the agent needs knowledge, it performs semantic retrieval.

---

# 12. 🔎 Semantic Product Retrieval

Products are also stored in the vector database.

Example:

```text
Product:
Sleep Better in 21 Days

Category:
Sleep

Description:
A structured 21-day program focused on
building healthier sleep routines.
```

The product is converted into an embedding:

```text
Product
   ↓
Embedding
   ↓
Qdrant
```

When Rahul shows strong sleep intent:

```text
User Interest

"Improve sleep and build a night routine"

        ↓

Vector Search

        ↓

Candidate Products

1. Sleep Better in 21 Days
2. Morning Routine Guide
3. Screen-Time Reset
4. Stress Management
```

---

# 13. 🗄️ Dual-Write Product Architecture

Every product must exist in:

```text
PostgreSQL
+
Qdrant
```

When an admin creates a product:

```text
Admin
  ↓
Product API
  ↓
┌─────────────────┐
│                 │
▼                 ▼
PostgreSQL       Qdrant
│                 │
Structured        Semantic
Data              Vector
```

---

# 14. 🔄 Product Synchronization

## Create

```text
Create Product
      ↓
PostgreSQL INSERT
      +
Qdrant UPSERT
```

## Update

```text
Update Product
      ↓
PostgreSQL UPDATE
      +
Qdrant UPDATE
```

## Delete

```text
Delete Product
      ↓
PostgreSQL DELETE
      +
Qdrant DELETE
```

The two stores should remain synchronized.

---

# 15. 🤖 Agentic Recommendation Engine

The core recommendation engine uses **LangGraph**.

The workflow is:

```text
User Activity
      ↓
Behavior Analysis
      ↓
Retrieve User Memory
      ↓
Retrieve Relevant Products
      ↓
Evaluate Retrieval
      ↓
Generate Recommendation
      ↓
Generate Persuasive Message
      ↓
Store Recommendation
```

Every **user-facing** LLM step (Recommendation Agent, Persuasion Agent, blood report summaries, coach chat) runs through the **privacy pipeline** before and after the Mesh API call:

```text
User text
      ↓
Presidio (mask PII)
      ↓
NeMo Guardrails (input)
      ↓
Mesh API (LLM) + structured biomarkers
      ↓
NeMo Guardrails (output)
      ↓
Presidio (de-anonymize)
      ↓
User-facing response
```

Internal agent steps (retrieval, scoring, memory updates) skip output guardrails and de-anonymization when `user_facing: false`.

---

# 16. 🧩 Behavior Agent

### Responsibilities

- Analyze user events
- Detect interest changes
- Identify high-intent behavior
- Summarize recent activity

Example:

```text
User has high and increasing interest
in sleep-related products.
```

---

# 17. 🧩 Memory Agent

### Responsibilities

- Retrieve relevant user memories
- Update long-term memories
- Identify previous successful recommendations

Example:

```text
Previous Recommendation:
Sleep Routine Guide

User:
Clicked → Started → Completed
```

The agent uses this information to improve future recommendations.

---

# 18. 🧩 Retrieval Agent

### Responsibilities

- Search Qdrant
- Retrieve relevant products
- Apply metadata filters
- Consider categories
- Consider price
- Return candidate products

Example:

```text
Query:
"Improve sleep and build night routine"

Top Results:

1. Sleep Better in 21 Days
2. Morning Routine Guide
3. Screen-Time Reset
```

---

# 19. 🧩 Evaluation Agent

Instead of blindly accepting the first vector-search results, candidates are evaluated using:

```text
Semantic Relevance
+
User Interest
+
Previous Behavior
+
Category Match
+
Price Fit
+
Historical Engagement
```

Example:

```text
Sleep Course
Relevance: 0.94

Morning Routine Guide
Relevance: 0.86

Stress Course
Relevance: 0.71
```

Only the strongest candidates continue.

---

# 20. 🧩 Recommendation Agent

The Recommendation Agent combines:

```text
User Behavior
+
Long-Term Memory
+
Product Candidates
+
RAG Knowledge
+
Optional Lifestyle Signals
+
Optional Report Signals
```

It determines:

```text
Primary Recommendation
Secondary Recommendation
Reason
Confidence
```

---

# 21. 🧩 Persuasion Agent

The recommendation is not just a product list.

The AI generates a short personalized narrative.

Example:

```text
You've been exploring sleep improvement
content several times today.

You also returned to this program after
viewing other options.

Because you seem to prefer structured,
step-by-step programs, "Sleep Better in
21 Days" looks like the strongest next
step for you.
```

Then:

```text
⭐ Sleep Better in 21 Days

₹499

Why recommended?

✓ You searched for sleep improvement
✓ You viewed this course twice
✓ High engagement with sleep content
✓ Matches your current interest

[View Course]
```

---

# 22. 🎯 Personalized Persuasion

Different users receive different messaging.

## Analytical User

```text
You've spent the most time on structured
sleep programs, and this course matches
that preference with a 21-day progression.
```

## Motivational User

```text
You've already taken the first step by
exploring better sleep.

Let's turn that interest into a 21-day
challenge.
```

## Busy User

```text
If you want a simple starting point,
this program gives you a structured plan
without requiring major lifestyle changes.
```

The product remains the same.

The **persuasion adapts to the user**.

---

# 23. 🔥 Recommendation Trigger System

AI should **not** run on every event.

### Bad Architecture

```text
Every click
   ↓
LLM
```

If a user generates 100 events:

```text
100 events
=
100 AI calls
```

This is expensive and inefficient.

### Good Architecture

```text
User Events
     ↓
Event Aggregation
     ↓
Detect Meaningful Change
     ↓
Check Cache
     ↓
AI Recommendation
```

Possible triggers:

```text
✓ User searches for a new topic

✓ User views multiple products
  from the same category

✓ User returns to a product

✓ Strong interest shift detected

✓ User manually requests recommendations

✓ Scheduled recommendation refresh
```

---

# 24. 💾 Recommendation Caching

Generated recommendations are stored.

Example:

```text
recommendations

id
user_id
product_ids
message
reason
created_at
expires_at
behavior_version
```

If the user's behavior has not changed significantly:

```text
Existing Recommendation
        ↓
Return Cached Result
```

No unnecessary AI call is required.

---

# 25. 🔄 Feedback Loop

Every recommendation creates feedback.

```text
Recommendation

      ↓

User Action

 ┌────┼─────┬────────┐
 ↓    ↓     ↓        ↓
View Click Save   Ignore
```

The system records:

```text
Recommendation:
Sleep Better in 21 Days

Displayed:
YES

Clicked:
YES

Started:
YES

Completed:
NO
```

This information becomes part of future recommendation logic.

---

# 26. 🧠 Continuous Learning Loop

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
RETRIEVE
   ↓
RECOMMEND
   ↓
PERSUADE
   ↓
OBSERVE RESPONSE
   ↓
UPDATE MEMORY
   ↓
RECOMMEND BETTER
   ↺
```

The system does not start from zero every time.

It becomes increasingly personalized.

---

# 27. 🏗️ Complete System Architecture

```text
                           USER
                             │
                             ▼
                    ┌─────────────────┐
                    │  Jinja2 + JS    │
                    │    Frontend     │
                    └────────┬────────┘
                             │
                     Behavioral Events
                             │
                             ▼
                    ┌─────────────────┐
                    │ Event Queue /   │
                    │ Batch Tracker   │
                    └────────┬────────┘
                             │
                             ▼
                          FastAPI
                             │
               ┌─────────────┴─────────────┐
               │                           │
               ▼                           ▼
         PostgreSQL                    Event Engine
               │                           │
               │                           ▼
               │                    Behavior Agent
               │                           │
               │                           ▼
               │                    User Interest
               │                           │
               └──────────────┬────────────┘
                              │
                              ▼
                         LangGraph
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
       Memory Agent     Retrieval Agent   RAG Agent
             │                │                │
             ▼                ▼                ▼
          Qdrant           Qdrant          Qdrant
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                       Evaluation Agent
                              │
                              ▼
                    Recommendation Agent
                              │
                              ▼
                       Persuasion Agent
                              │
                              ▼
                    Privacy Pipeline
              (Presidio → NeMo → LLM → NeMo → Presidio)
                              │
                              ▼
                          Mesh API
                              │
                              ▼
                  Personalized Recommendation
                              │
                              ▼
                           Frontend
                              │
                              ▼
                       User Feedback
                              │
                              ▼
                        Memory Update
                              │
                              └───────────────↺
```

---

# 28. 🛠️ Technology Stack

## Backend

**FastAPI**

Required by the challenge.

## Frontend

**Jinja2 + JavaScript**

Used for:

- Event tracking
- Search
- Product interactions
- Dynamic recommendations
- Async API calls

## AI

**Mesh API**

All AI/LLM calls must go through Mesh API.

## Privacy & Safety

**Presidio** (embedded)

PII/PHI detection, tokenization, and de-anonymization before and after external LLM calls.

**NeMo Guardrails** (embedded)

Programmable wellness-only safety policies on input and user-facing output.

**spaCy** (`en_core_web_lg`)

NLP engine for Presidio entity detection, plus custom Indian lab-report recognizers.

## Agent Framework

**LangGraph**

Used for explicit agentic workflows.

## Vector Database

**Qdrant**

Used for:

- Product embeddings
- User memory
- Semantic retrieval
- RAG

## Database

**PostgreSQL**

Used for:

- Users
- Products
- Events
- Recommendations
- Feedback
- Health profiles
- Report metadata

## Scheduler

**APScheduler**

Used for proactive recommendation delivery.

## Observability

**LangSmith**

Used for tracing the agent workflow.

---

# 29. 📊 Database Schema

## users

```text
id
name
email
password_hash
role
created_at
```

## products

```text
id
title
description
category
price
metadata
created_at
updated_at
```

## events

```text
id
user_id
event_type
product_id
metadata
timestamp
```

## recommendations

```text
id
user_id
message
product_ids
reason
confidence
created_at
expires_at
```

## feedback

```text
id
user_id
recommendation_id
action
timestamp
```

## health_profiles

```text
id
user_id
sleep_average
steps_average
water_average
screen_time_average
updated_at
```

## blood_reports

```text
id
user_id
file_name
upload_date
extracted_data
```

---

# 30. 👑 User Roles

## Regular User

Can:

- Browse products
- Search
- View products
- Receive recommendations
- See recommendation explanations
- Provide feedback
- View personal behavioral insights
- Upload optional wellness reports

## Admin

Can:

- Add products
- Edit products
- Delete products
- View catalog
- Trigger vector synchronization
- Monitor recommendation statistics

---

# 31. 🖥️ Main Screens

## Home

```text
HealthPilot AI

Discover wellness products
personalized for you.

[Explore]
```

## Product Marketplace

```text
Sleep
Fitness
Nutrition
Mental Wellness
Lifestyle
```

## Product Details

```text
Sleep Better in 21 Days

₹499

Description...

[Start]
[Add to Wishlist]
```

## AI Recommendations

```text
✨ Recommended For You

Based on what you've explored today...

⭐ Sleep Better in 21 Days

Why?

✓ Strong sleep interest
✓ High engagement
✓ Repeated visits

[View Course]
```

## My AI Profile

```text
🧠 What HealthPilot Has Learned

Primary Interest:
Sleep

Preferred Content:
Structured Programs

Engagement:
High

Recent Interest:
Stress Management

Favorite Time:
Evening
```

## Optional Health Profile

```text
Health Insights

Sleep
5.3h average

Steps
2,200/day

Water
1.4L/day

[Upload Report]
```

## Progress / Activity

```text
Your Activity

Products Viewed
24

Searches
8

Recommendations
5

Recommendations Clicked
3

Current Interest
Sleep & Recovery
```

---

# 32. 📧 Proactive Recommendations

As a bonus feature, HealthPilot can send a scheduled recommendation digest.

Example:

```text
Good Evening Rahul 👋

You explored sleep and wellness
content several times today.

We found 3 recommendations that
match your current interests.

1. Sleep Better in 21 Days
2. Morning Routine Guide
3. Screen-Time Reset

[View My Recommendations]
```

This runs automatically using:

```text
APScheduler / Celery
```

It is not a manual "Send Email" button.

---

# 33. 🔍 Observability

Using LangSmith, visualize:

```text
User Event
     ↓
Behavior Analysis
     ↓
Memory Retrieval
     ↓
Product Retrieval
     ↓
Re-ranking
     ↓
Recommendation
     ↓
Privacy Pipeline (Presidio → NeMo → LLM → NeMo → Presidio)
     ↓
Persuasion
     ↓
Final Response
```

Track:

- Latency
- AI calls
- Retrieval quality
- Token usage
- Failures
- Recommendation generation time

---

# 34. 🚀 Retrieval Improvements

### Basic

```text
Vector Search
      ↓
Top 5 Products
```

### Advanced

```text
Vector Search
      ↓
Metadata Filtering
      ↓
Candidate Products
      ↓
Re-ranking
      ↓
Behavior Score
      ↓
Final Top 3
```

Potential ranking formula:

```text
Final Score =

Semantic Similarity
+
Behavior Relevance
+
Category Relevance
+
Engagement Score
+
Previous Success
```

---

# 35. ⚡ Production Thinking

HealthPilot is designed to avoid unnecessary AI usage.

### Event batching

```text
100 browser events
       ↓
10 meaningful batches
```

### AI trigger detection

```text
100 events
       ↓
3 meaningful behavior changes
       ↓
3 AI calls
```

### Recommendation caching

```text
Same behavior
     ↓
Cached recommendation
     ↓
No LLM call
```

### Background processing

Heavy tasks such as:

- Embedding
- Report parsing
- Recommendation refresh
- Email delivery

can run asynchronously.

---

# 36. 🔒 PII & PHI Handling (Presidio)

HealthPilot handles blood reports, chat, behavioral notes, and recommendation text that mix **PII** and **PHI**.

## Definitions

**PII** — direct personal identifiers in free text:

- Names
- Phone numbers
- Email addresses
- Government IDs (e.g. Aadhaar)
- Patient / lab IDs on pathology reports

**PHI** — health information linked to an identifiable person:

- Biomarkers when embedded in narrative text
- Diagnoses, provider names, dates of service
- Any PII appearing on medical documents

## Tiered data handling

HealthPilot uses a **tiered** approach:

```text
Free text (chat, OCR, persuasion context)
      ↓
Presidio de-identification
      ↓
Token placeholders sent to external LLM

Biomarkers (HbA1c, Vitamin D, LDL, etc.)
      ↓
Structured JSON fields in PostgreSQL
      ↓
Injected into LLM prompts as structured data only
```

Raw blood report text and direct identifiers **never** cross the external LLM boundary.

## Presidio responsibilities

Presidio (embedded in the FastAPI backend) is responsible for **entity detection only**, not conversational policy.

It:

- Detects PII/PHI entities using spaCy NER + custom recognizers
- Replaces identifiers with reversible tokens (e.g. `{{PERSON_1}}`)
- Stores mappings in a **token vault** for de-anonymization after output guardrails pass
- Restores original identifiers in the final user-facing response

Custom recognizers cover Indian context:

```text
IN_PHONE        Indian mobile numbers
IN_AADHAAR      Aadhaar numbers
LAB_PATIENT_ID  Lab / sample IDs
MEDICAL_RECORD_NUMBER  MRN, UHID, IPD, OPD numbers
```

## Example

**User input:**

```text
Hi, I am Rahul. My phone is 9876543210.
What sleep programs fit my HbA1c of 6.2?
```

**After Presidio (sent to LLM):**

```text
Hi, I am {{PERSON_1}}. My phone is {{IN_PHONE_1}}.
What sleep programs fit my HbA1c of 6.2?
```

**Structured biomarkers in prompt (separate field):**

```json
{ "hba1c": 6.2 }
```

**After de-anonymization (returned to user):**

```text
Hi Rahul, based on your interest in sleep programs...
```

## Failure behavior

If Presidio is unavailable, **all external LLM calls are blocked**. No raw PII may reach Mesh API as a fallback.

---

# 37. 🛡️ NeMo Guardrails

**NeMo Guardrails** (embedded in the FastAPI backend) enforces programmable safety policies. It handles **conversational policy and blocking** — not entity detection (that is Presidio's job).

Config location: `src/healthPilot/privacy/nemo_config/config.yml`

NeMo LLM settings (judge model) come from `.env`:

```text
NEMO_LLM_BASE_URL
NEMO_LLM_API_KEY
NEMO_LLM_MODEL
```

## Policy scope

HealthPilot is a **wellness recommendation platform**, not a medical diagnosis system.

NeMo must **allow**:

- Lifestyle and wellness coaching
- General wellness relevance of biomarkers (e.g. "your Vitamin D is on the lower side")
- Educational context from RAG knowledge

NeMo must **block**:

- Diagnosis requests ("Do I have diabetes?")
- Prescription or dosage advice
- Emergency medical triage (redirect to emergency services)
- Harmful, illegal, or abusive content
- Claims that replace a healthcare professional

## Rail placement (hybrid)

```text
Global input rail
      ↓
At graph entry — every path to an external LLM

Output rails
      ↓
User-facing agents only:
  • Recommendation Agent
  • Persuasion Agent
  • AI Coach / chat
  • Blood report summaries shown to users

Skipped when user_facing: false
  • Internal retrieval / scoring / memory agents
```

## Input vs output checks

**Input rail** validates de-identified user text before the LLM call.

**Output rail** validates the LLM response before it is shown, persisted, or emailed to the user.

Blocked content returns a safe refusal (HTTP 422) — never raw LLM output that violates policy.

## Failure behavior

If NeMo is unavailable on a **user-facing** path, the response is blocked. Internal agent paths may proceed without output rails when explicitly marked non-user-facing.

---

# 38. 🔐 Privacy Pipeline

The **privacy pipeline** is the mandatory sequence for every user-facing LLM call.

```text
User input
      ↓
Presidio (PII detection + masking)
      ↓
NeMo Guardrails (input validation)
      ↓
Mesh API (LLM) + structured biomarkers
      ↓
NeMo Guardrails (output validation)
      ↓
Presidio (de-anonymization)
      ↓
User response
```

## Fixed order

```text
Presidio → NeMo input → LLM → NeMo output → Presidio de-anonymize
```

This order is **not optional**:

- Guardrails and the LLM **never** see raw PII
- De-anonymization runs **only after** output guardrails pass
- Biomarkers enter prompts as structured fields, not as raw report OCR text

## LangGraph integration

The privacy pipeline is implemented as LangGraph nodes:

```text
START
  → presidio_deidentify
  → guardrail_input
  → llm_call
  → guardrail_output
  → presidio_deanonymize
  → END
```

Recommendation and persuasion agents invoke this graph (or equivalent pipeline steps) before returning text to the frontend, email digest, or any external channel.

## Deployment

Presidio and NeMo run **in-process** inside the FastAPI backend (no separate Docker services required for the privacy layer). Both engines warm up on backend startup.

## External LLM boundary

The **external LLM boundary** is the point where text leaves HealthPilot infrastructure and reaches Mesh API. All free text must be de-identified **before** crossing this boundary.

---

# 39. 🩸 Blood Report Safety

The blood report feature is an **optional personalization feature**, not a diagnostic engine.

HealthPilot should:

- Extract information
- Present the extracted values
- Explain general wellness relevance using trusted sources
- Use information as recommendation context
- Encourage professional consultation when appropriate

HealthPilot should NOT:

- Diagnose diseases
- Prescribe medication
- Change medication dosage
- Replace a doctor
- Claim certainty about medical conditions

---

# 40. 🔐 Privacy & Security

Sensitive information should be protected at every layer.

## Privacy pipeline (mandatory)

All user-facing LLM text follows:

```text
Presidio → NeMo input → LLM → NeMo output → Presidio de-anonymize
```

See sections **36–38** for full PII, guardrails, and pipeline details.

## Data minimization

- Store only what is needed for recommendations and memory
- Keep biomarkers in structured PostgreSQL fields, not duplicated in free-text logs
- De-identify chat, OCR, and persuasion context before Mesh API
- Token vault mappings are session-scoped and used only for de-anonymization

## Application security

Implement:

- Password hashing
- Environment variables for API keys (`.env`, never committed)
- HTTPS in production
- Access-controlled blood reports and health profiles
- User-owned data with delete/export support
- Secure file handling for uploaded PDFs and images
- No API keys in frontend
- `.env` excluded from Git

Example `.gitignore`:

```text
.env
.env.*
__pycache__/
*.pyc
```

---

# 41. 🏅 Challenge Requirement Mapping

| SmartReco Requirement | HealthPilot Implementation |
|---|---|
| Web platform | Jinja2 + JavaScript |
| User login | Email/password |
| Admin role | Product management dashboard |
| Product catalog | Wellness courses/programs/products |
| SQL database | PostgreSQL |
| Vector DB | Qdrant |
| Dual-write | PostgreSQL + Qdrant |
| Behavioral tracking | JavaScript event tracker |
| Efficient events | Batching + throttling |
| Semantic retrieval | Qdrant |
| RAG | Wellness knowledge base |
| Agentic AI | LangGraph |
| Personalized recommendation | Recommendation Agent |
| Persuasive messaging | Persuasion Agent |
| Behavior adaptation | Feedback + memory |
| Mesh API | All AI calls |
| AI efficiency | Triggering + caching |
| Scheduled delivery | APScheduler |
| Observability | LangSmith |
| Retrieval polish | Filtering + reranking |
| Optional personalization | Lifestyle + blood report |
| PII protection | Presidio de-identification before Mesh API |
| Safety guardrails | NeMo Guardrails (input + user-facing output) |
| Privacy pipeline | Presidio → NeMo → LLM → NeMo → Presidio |
| Tiered health data | Structured biomarkers only in LLM prompts |

---

# 42. ⭐ Bonus Features

## ⭐ LangGraph

Explicit multi-step agent workflow.

## ⭐ Scheduled Delivery

Daily personalized recommendation digest.

## ⭐ LangSmith

End-to-end agent tracing.

## ⭐ Retrieval Re-ranking

Improves product relevance.

## ⭐ Behavioral Memory

Long-term user preference learning.

## ⭐ Recommendation Explainability

Shows exactly why a product was recommended.

## ⭐ Optional Blood Report

Additional personalization signal.

## ⭐ Privacy Pipeline

Presidio + NeMo Guardrails on every user-facing LLM call.

## ⭐ PII De-identification

Direct identifiers masked before Mesh API; restored after output validation.

---

# 43. 🔮 Future Enhancements

- Google Fit integration
- Apple Health integration
- Smartwatch integration
- Telegram recommendations
- WhatsApp recommendations
- Voice AI wellness coach
- Personalized meal plans
- Habit prediction
- Multi-language recommendations
- Advanced recommendation analytics
- A/B testing of persuasion strategies
- Contextual bandit-based recommendation optimization

---

# 44. 🛡️ Responsible AI

HealthPilot is designed as a **wellness recommendation platform**, not a medical diagnosis system.

The system should clearly communicate:

> HealthPilot AI provides educational and wellness-oriented recommendations based on the information provided by the user. It does not diagnose medical conditions, prescribe medication, or replace professional medical advice.

## Guardrails enforcement

Safety is enforced in code, not only in prompts:

- **Presidio** strips direct identifiers before text reaches Mesh API
- **NeMo Guardrails** blocks diagnosis, prescription, and emergency-triage requests on input and user-facing output
- **Structured biomarkers** allow wellness context without sending raw lab report text to the LLM
- Blocked responses return a safe refusal — never unvalidated LLM output

## User data controls

For sensitive health information:

- Minimize stored data
- Protect uploaded files
- Use authentication and authorization
- Give users control over their information
- Allow users to delete their data and AI memories

---

# 45. 🏆 Why HealthPilot AI Stands Out

Most recommendation systems answer:

> **"What products are similar?"**

HealthPilot answers:

> **"What is this user currently trying to achieve, and what should they do next?"**

The system combines:

```text
Behavior
   +
Intent
   +
Memory
   +
Semantic Retrieval
   +
RAG
   +
Product Catalog
   +
Personalization
   +
Persuasion
   +
Privacy Pipeline
   +
Feedback
```

This creates a recommendation engine that doesn't just recommend products.

It **understands the user's journey and continuously adapts to it.**