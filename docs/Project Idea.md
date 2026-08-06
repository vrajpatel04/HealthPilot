# 🩺 HealthPilot AI
### An Agentic AI Lifestyle Recommendation System with Behavioral Intelligence, Blood Report Analysis, RAG & Long-Term Memory

---

# 🚀 Problem Statement

Traditional health and fitness apps provide **generic recommendations** such as:

- Sleep 8 hours
- Drink 2L water
- Exercise daily
- Eat healthy

These recommendations ignore:

- User behavior
- Personal habits
- Medical reports
- Motivation style
- Lifestyle patterns

As a result, users quickly lose interest because the recommendations don't feel personal.

---

# 💡 Solution

**HealthPilot AI** is an **Agentic AI Health Coach** that continuously learns about the user.

Unlike traditional apps, it combines

- 🧠 Daily behavior tracking
- 🩸 Blood report analysis
- 📚 Medical RAG
- 🧠 Long-term memory
- 🤖 Multiple AI agents
- 📈 Continuous learning

to generate **personalized, explainable and persuasive wellness recommendations.**

---

# 🎯 Vision

Our AI behaves like a real health coach.

Instead of saying

> Drink more water.

it says

> Yesterday you only drank **1.2L** of water.
>
> Your blood report also shows slightly elevated HbA1c.
>
> Since you usually complete small goals, let's aim for **2L today** by drinking one glass before every meal.

The recommendation becomes

- Personalized
- Evidence-backed
- Behavior-aware
- Easy to follow

---

# 👤 User Journey

## Step 1

User creates an account.

---

## Step 2

Uploads their blood report.

Supported

- PDF
- Image

Example

```
HbA1c : 6.2

Vitamin D : 14

LDL : 162

HDL : 38

Triglycerides : 230
```

---

## Step 3

User logs daily activities

- Sleep
- Water intake
- Food
- Walking
- Screen time
- Mood

---

## Step 4

Behavior Tracker continuously records

- Daily habits
- Recommendation acceptance
- Goal completion
- App usage
- Improvement trends

---

## Step 5

AI generates

Today's Personalized Wellness Plan

Example

```
Good Morning Rahul 👋

Today's Priorities

🚶 Walk 4000 steps

🥤 Drink 2L water

🌞 Spend 20 minutes outdoors

🌙 Sleep before 11 PM

Reason

These recommendations are based on

✓ Your blood report

✓ Your recent activity

✓ Your lifestyle patterns

✓ Trusted health knowledge
```

---

# 🧠 Core Modules

## 1️⃣ Blood Report Analysis

Users upload

- CBC
- Lipid Profile
- Vitamin Reports
- Diabetes Reports
- Liver Function
- Kidney Function
- Any standard pathology report

---

### AI extracts biomarkers

Example

```json
{
    "HbA1c":6.2,
    "Vitamin D":14,
    "LDL":162,
    "HDL":38,
    "Triglycerides":230
}
```

These biomarkers become part of the user's health profile.

---

## 2️⃣ Daily Lifestyle Tracking

User logs

- Sleep
- Water
- Steps
- Food
- Mood
- Screen Time

Later versions may integrate

- Google Fit
- Apple Health
- Smart Watch

---

## 3️⃣ Behavioral Tracking

The system learns

- Which goals users complete
- Which reminders they ignore
- Best workout timing
- Water drinking habits
- Weekend lifestyle
- Motivation style

Example

```
AI Learned

Prefers evening walks

Sleeps late on weekends

Responds well to small goals

Frequently skips breakfast

Drinks sugary beverages during office hours
```

---

# 🤖 Agentic AI Architecture

Instead of one chatbot,

multiple specialized AI agents collaborate.

---

## Agent 1

### Blood Report Analysis Agent

Responsibilities

- Read uploaded reports
- Extract biomarkers
- Normalize values
- Detect health indicators
- Build structured health profile

Output

```
HbA1c

High

Vitamin D

Low

LDL

High
```

---

## Agent 2

### Behavior Analysis Agent

Analyzes

- Sleep
- Walking
- Water
- Screen time
- Food habits

Generates

```
Sleep Pattern

Poor

Activity Level

Low

Hydration

Poor

Sugar Intake

High
```

---

## Agent 3

### Memory Agent

Stores

Long-term behavior

Example

```
Rahul

Average Sleep

5.4h

Average Steps

2200

Motivation

Progress Based

Preferred Workout

Walking

Weekend Eating

Poor
```

Memory improves every day.

---

## Agent 4

### RAG Retrieval Agent

Retrieves trusted medical knowledge.

Knowledge Sources

- Sleep Guidelines
- Nutrition Guidelines
- WHO Wellness Recommendations
- Hydration Information
- Physical Activity Guidelines
- Blood Biomarker Information
- Healthy Recipes

Instead of relying only on the LLM,

the AI retrieves relevant documents first.

---

## Agent 5

### Recommendation Agent

Combines

Blood Report

+

Behavior

+

Memory

+

Medical Knowledge

↓

Creates

Today's priorities.

---

## Agent 6

### Persuasion Agent

Different users receive different motivation.

Example

Analytical User

> Walking after meals can support healthy blood sugar management.

Motivational User

> You're only 900 steps away from beating yesterday.

Busy User

> Just a 15-minute walk after dinner today is a great start.

---

## Agent 7

### Feedback Agent

Learns

Did user

- Accept recommendation?
- Ignore recommendation?
- Complete goal?

Feedback updates memory.

---

# 🔄 Complete AI Workflow

```text
                        USER

                          │

        ┌─────────────────┴─────────────────┐

        │                                   │

 Blood Report Upload              Daily Lifestyle Logs

        │                                   │

        ▼                                   ▼

 OCR + Report Parser              Behavior Tracker

        │                                   │

        ▼                                   ▼

 Blood Report Agent             Behavior Analysis Agent

        └──────────────┬────────────────────┘

                       ▼

             User Health Profile

                       ▼

             Long-Term Memory Agent

                       ▼

             Embedding Generation

                       ▼

                Qdrant Vector DB

                       ▼

                 RAG Retrieval

                       ▼

                 Trusted Health
                  Knowledge

                       ▼

                  Mesh API (LLM)

                       ▼

            Recommendation Agent

                       ▼

             Persuasion Agent

                       ▼

        Personalized Daily Wellness Plan

                       ▼

               User Feedback

                       ▼

             Memory Updated

                       ▼

                     Repeat
```

---

# 📚 RAG Knowledge Base

The AI retrieves trusted health information before generating recommendations.

Knowledge includes

- Sleep Hygiene
- Hydration
- Walking Benefits
- Healthy Nutrition
- WHO Wellness Guidelines
- Vitamin D Information
- HbA1c Lifestyle Guidance
- Cholesterol Lifestyle Guidance
- Mental Wellness
- Stress Management
- Healthy Recipes

---

# 🧠 Memory System

## Session Memory

Temporary information

```
Today

Sleep

5h

Water

800ml

Mood

Tired

Steps

1200
```

---

## Long-Term Memory

Persistent knowledge

```
Average Sleep

5.5 hours

Average Water

1.4L

Prefers Small Goals

Weekend Binge Eating

Evening Walker

High Screen Time

Responds Better to Encouragement

Uploaded Blood Reports

Latest Biomarker Summary
```

---

# 💾 Databases

## PostgreSQL

Stores

- Users
- Daily Logs
- Blood Report Metadata
- Goals
- Feedback
- Recommendations
- Events

---

## Qdrant

Stores

- User Memories
- Behavioral Patterns
- Blood Report Embeddings
- Medical Knowledge
- Lifestyle Documents

---

# 📱 Application Screens

## Dashboard

Shows

- Sleep
- Water
- Steps
- Screen Time
- Mood
- Today's AI Plan

---

## Blood Report Upload

Upload

- PDF
- Image

Displays

Extracted biomarkers

AI Summary

---

## Daily Logger

Log

- Sleep
- Water
- Food
- Steps
- Mood

---

## AI Coach

Shows

Today's recommendations

Reason behind recommendation

Retrieved health evidence

---

## My AI Memory

Displays

```
AI has learned

✓ You prefer evening walks

✓ Small goals work best

✓ Low Vitamin D trend

✓ High sugar intake on weekends

✓ Walking goals completed 82%
```

Users can edit or delete memories.

---

## Progress Dashboard

Weekly charts

- Sleep
- Water
- Steps
- Mood
- Goal Completion
- Blood Marker Trends (when multiple reports are uploaded)

---

# 🛠️ Tech Stack

## Frontend

- Next.js
- Tailwind CSS
- ShadCN UI

---

## Backend

- FastAPI

---

## Agent Framework

- LangGraph

---

## AI Provider

- Mesh API (All AI Calls)

---

## Database

- PostgreSQL

---

## Vector Database

- Qdrant

---

# ⭐ Key Features

- ✅ Agentic AI Architecture
- ✅ Blood Report Analysis
- ✅ Behavioral Intelligence
- ✅ Long-Term Memory
- ✅ Session Memory
- ✅ RAG with Trusted Wellness Knowledge
- ✅ Vector Search using Qdrant
- ✅ Personalized Daily Wellness Plans
- ✅ Persuasive Recommendation Generation
- ✅ Explainable AI Recommendations
- ✅ Continuous Learning through Feedback
- ✅ Blood Marker Trend Tracking

---

# 🚀 Future Enhancements

- Google Fit Integration
- Apple Health Integration
- Smart Watch Sync
- AI Voice Health Coach
- Weekly AI Health Reports
- Personalized Meal Planning
- Medication Reminder Integration
- Family Health Dashboard
- Multi-language Support
- Predictive Lifestyle Risk Trends (wellness-focused)

---

# ⚠️ Disclaimer

HealthPilot AI is designed to provide **personalized lifestyle and wellness recommendations** using user behavior, uploaded blood reports, and trusted health information.

It **does not diagnose diseases, prescribe medication, or replace professional medical advice**. Users should always consult qualified healthcare professionals for diagnosis or treatment decisions.

---

# 🏆 Why HealthPilot AI Stands Out

HealthPilot AI goes beyond a traditional chatbot or fitness tracker by combining **behavioral intelligence, document understanding, retrieval-augmented generation (RAG), long-term memory, and agentic AI** into a single personalized wellness platform.

Rather than giving the same advice to every user, the system continuously learns from daily habits, understands laboratory reports, retrieves trusted wellness knowledge, and adapts its coaching style based on what motivates each individual. This creates a production-style AI assistant that becomes smarter over time while remaining transparent, explainable, and user-centric.