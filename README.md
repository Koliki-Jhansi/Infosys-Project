# AeroAssist AI

**Intelligent Airport & Airways Customer Support Platform**  
*Multi-Agent Aviation Support System with RAG Resolution & Quality Gate*

---

## Project Overview

**AeroAssist AI** is a multi-agent customer support web platform tailored specifically for the **Airport & Airways Passenger Support Domain**. Adapted from intelligent support architectures, all domain models, knowledge clusters, classification rules, UI interfaces, and resolution workflows are dedicated to commercial aviation and passenger logistics.

```
Passenger
    ↓
Airport Support Website
    ↓
Support Ticket
    ↓
Flask Backend
    ↓
AI Classification & Urgency Engine
    ↓
Knowledge Retrieval (TF-IDF + Cosine Similarity)
    ↓
Multi-Agent Resolution Pipeline (5 Sequential Agents)
    ↓
Validation Gate (70% Confidence Threshold)
    ↓
AUTO_RESOLVE  ──OR──  ESCALATE (Human Support Handoff)
```

---

## Problem Statement

Airport and airline passenger desks experience high volumes of repetitive inquiries regarding delayed luggage, web check-in failures, flight cancellations, wheelchair accessibility, airport lounges, and payment confirmations. Manual handling causes delays, customer friction, and escalation bottlenecks. 

Generic AI chatbots often hallucinate operational decisions (e.g., claiming refunds are approved or inventing flight status). AeroAssist AI solves this by deploying a **grounded 5-agent sequential resolution pipeline** with a strict mathematical **quality validation gate** to safely auto-resolve verified procedural inquiries while seamlessly escalating edge cases to human personnel.

---

## Proposed Solution

AeroAssist AI provides an integrated 3-Milestone solution:
1. **Milestone 1**: Passenger ticket management, SQLite persistence, and machine-learning category classification + priority/severity evaluation.
2. **Milestone 2**: Aviation-domain RAG retrieval engine powered by `TfidfVectorizer` and `cosine_similarity` over 7 curated airport knowledge clusters (25 procedural articles).
3. **Milestone 3**: Five-agent sequential orchestration (Diagnosis → Retrieval → Resolution → Validation → Escalation) governed by a 70% weighted confidence quality gate.

---

## Milestone Breakdown

### Milestone 1: Passenger Support & Ticket Management
- **Domain Identity & Authentication**: Aviation-themed glassmorphism interface with session authentication and instant one-click demo logins (Passenger, Agent, Admin).
- **Airport Support Categories (9 Domains)**:
  1. Booking & Confirmation
  2. Check-in & Boarding
  3. Baggage
  4. Delays & Cancellations
  5. Refunds & Payments
  6. Airport Facilities
  7. Shopping & Services
  8. Passenger Assistance
  9. General Support
- **Ticket Fields & Metadata**: `ticket_id` (`TKT-xxx`), passenger details, issue title, description, category, priority, severity, status, `flight_number`, `booking_ref` (PNR), `airport`, `travel_date`.
- **Classification Engine**: `scikit-learn` TF-IDF Vectorizer + Multinomial Naive Bayes trained on domain queries with calibrated probability estimation.
- **Priority & Severity Evaluation**: Rule-based urgency scoring identifying critical travel disruptions, proximity to travel date, and accessibility requirements.
- **SQLite Persistence**: Clean data layer managing `users`, `tickets`, and `agent_runs` audit logs.

### Milestone 2: Airport Knowledge Resolution / RAG
- **7 Knowledge Base Clusters (25 Articles `KB001` - `KB025`)**:
  - `FLIGHTS`: Schedules, delays, cancellations, rebooking, boarding gate rules.
  - `CHECK-IN & BOARDING`: Web check-in troubleshooting, self-service kiosks, security screening (LAG / prohibited items).
  - `BAGGAGE`: Delayed baggage PIR files, lost luggage claims, damaged luggage DIR, cabin allowances, oversize items.
  - `AIRPORT FACILITIES`: Lounges, short/long-term parking, terminal transfers, shuttles.
  - `SHOPPING & SERVICES`: Duty-free tax-free allowances, restaurants/food courts, VAT export refund desk.
  - `BOOKING & PAYMENT`: E-tickets, PNR confirmation, payment failures/double charge reconciliation, fare refunds.
  - `PASSENGER ASSISTANCE`: Wheelchair assistance (WCHR/WCHS/WCHC), senior escorts, unaccompanied minors, airport lost-and-found.
- **TF-IDF + Cosine Similarity Retriever**: `TfidfVectorizer` (unigrams+bigrams, sublinear TF) + `cosine_similarity` ranking with configurable similarity threshold (default 20%).
- **Context Builder & Resolution Generator**: Formulates grounded, structured passenger instructions without hallucinating live operational data.

### Milestone 3: Multi-Agent Airport Support
- **Five Sequential Agents**:
  1. **Diagnosis Agent**: Identifies passenger intent, category, and extracts flight/PNR entities with diagnosis confidence ($S_{diag}$).
  2. **Retrieval Agent**: Reuses Milestone 2 TF-IDF + Cosine retriever, returning matched knowledge articles and similarity score ($S_{ret}$).
  3. **Resolution Agent**: Formulates step-by-step resolution grounded in retrieved support procedures, computing resolution completeness ($S_{comp}$).
  4. **Validation Agent (Quality Gate)**: Calculates weighted confidence score across all 3 signals.
  5. **Escalation Agent**: Applies decision threshold to route ticket to either `AUTO_RESOLVE` or `ESCALATE`.
- **Weighted Confidence Formula**:
  $$\text{Final AI Confidence} = S_{diag} \times 0.40 + S_{ret} \times 0.40 + S_{comp} \times 0.20$$
- **Decision Gate Logic**:
  - **$\text{Final Confidence} \ge 70.0\%$** $\implies$ **`AUTO_RESOLVE`** (Passenger receives resolution directly; no Jira/email escalation).
  - **$\text{Final Confidence} < 70.0\%$** $\implies$ **`ESCALATE`** (Human support handoff preserving complete AI diagnostic context).
- **Modular Integrations**: Jira REST service (`jira_service.py`) and SMTP email alert service (`email_service.py`) configured via environment variables, reporting genuine integration status without fabricating fake issue keys or fake emails.

---

## Passenger Journey

```
PASSENGER
Raises Support Issue (e.g. Baggage / Check-in)
        ↓
AIRPORT WEBSITE
Stores Ticket in SQLite (TKT-001)
        ↓
AI CLASSIFICATION & URGENCY
Assigns Category, Priority & Severity
        ↓
RAG KNOWLEDGE RETRIEVAL
Searches 25 Knowledge Base Articles across 7 Clusters
        ↓
MULTI-AGENT WORKFLOW
[Diagnosis] → [Retrieval] → [Resolution] → [Validation] → [Escalation]
        ↓
VALIDATION GATE
Calculates Final AI Confidence = (0.40×Diag + 0.40×Ret + 0.20×Comp)
        ↓
DECISION GATE
        ├── If >= 70%  ──►  AUTO_RESOLVE (Resolution provided to passenger)
        └── If < 70%   ──►  HUMAN SUPPORT (Escalated with AI context preserved)
```

---

## Project Structure

```
AeroAssist/
├── app.py                      # Flask Application Routes & Authentication
├── database.py                 # SQLite Schema, User/Ticket CRUD & Agent Audit Logs
├── classifier.py               # Scikit-Learn TF-IDF + Naive Bayes Classifier
├── priority.py                 # Aviation Urgency & Proximity Priority Engine
├── severity.py                 # Operational Impact Assessment Engine
├── status.py                   # Ticket Lifecycle State Manager
├── agents.py                   # 5-Agent Sequential Architecture & Orchestrator
├── jira_service.py             # Modular Jira API Service (Environment-driven)
├── email_service.py            # Modular SMTP Email Alert Service (Environment-driven)
├── requirements.txt            # Python Dependencies
├── .env.example                # Environment Configuration Template
├── .gitignore                  # Git Ignore Configuration
├── test_aeroassist.py          # Unit Test Suite for Milestones 1, 2, and 3
├── test_functional.py          # Functional HTTP Client Test Suite
├── verify_live_server.py       # Live Server End-to-End Verification Script
│
├── data/
│   ├── airport_knowledge_base.json  # 25 KB Articles across 7 Clusters
│   └── training_dataset.json        # Training Dataset for 9 Domain Categories
│
├── rag/
│   ├── __init__.py             # RAG Package Initializer
│   ├── knowledge_base.py       # KB Loader & Cluster Manager
│   ├── retriever.py            # TF-IDF + Cosine Similarity Vector Retriever
│   └── pipeline.py             # Context Builder & Resolution Generator
│
├── templates/
│   ├── base.html               # Master Aviation Glassmorphism Layout
│   ├── login.html              # Sign In, Registration & One-Click Demo Logins
│   ├── dashboard.html          # Stats, From-Ticket-To-Outcome Journey, Recent Tickets
│   ├── tickets.html            # Ticket List with Filters, Search & Categories
│   ├── create_ticket.html      # Ticket Creation with Quick-Fill Scenario Chips
│   ├── ticket_detail.html      # Ticket Details, Classification Breakdown & Audit Logs
│   ├── ai_resolution.html      # Interactive 5-Agent Resolution Studio & Quality Gauge
│   └── knowledge_base.html     # Knowledge Base Explorer (7 Clusters & Search)
│
└── static/
    ├── css/
    │   └── aeroassist.css      # Custom Aviation Design System
    └── js/
        └── aeroassist.js       # Live Multi-Agent Execution & UI Animations
```

---

## Installation & Setup

### 1. Clone & Navigate
```bash
cd AeroAssist
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` (optional, defaults run in secure local mode):
```bash
cp .env.example .env
```

---

## Running the Application

Start the Flask development server:
```bash
python app.py
```

Access the application in your browser:
**`http://127.0.0.1:5000`**

### Instant Demo Accounts
| Role | Username | Password | Purpose |
|------|----------|----------|---------|
| **Passenger** | `passenger` | `pass123` | Raise tickets, view passenger status |
| **Support Agent** | `agent` | `agent123` | Manage tickets, run AI resolution |
| **Admin** | `admin` | `admin123` | Full system oversight |

*Or click the **"Instant One-Click Demo Logins"** on the login page.*

---

## Running Automated Tests

Run the Milestone 1, 2, 3 unit test suite:
```bash
python test_aeroassist.py
```

Run functional integration tests:
```bash
python test_functional.py
```

Run end-to-end live server verification:
```bash
python verify_live_server.py
```

---

## Security & Reliability

- **No Hard-coded Credentials**: All external integration settings (Jira, SMTP) are loaded strictly via environment variables.
- **No Fabricated Data**: If Jira or SMTP are unconfigured, the system reports `"Not Configured"` rather than generating fake ticket IDs.
- **Grounded AI Generation**: Resolutions are strictly derived from verified procedural articles to prevent hallucinations regarding real-time flight status, gate changes, or compensation approvals.
- **SQL Parameterization**: Parameterized queries across SQLite operations prevent SQL injection.
