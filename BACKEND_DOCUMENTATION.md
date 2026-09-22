# 🚆 MahaTransit AI – Complete Backend Architecture & System Documentation

> **Project:** MahaTransit AI (Intelligent Public Transport Complaint Management System)  
> **Target Transport Networks:** Mumbai Metro, BEST Buses, Mumbai Local Trains (Central & Western Railways)  
> **Backend Framework:** FastAPI (Python 3.10+)  
> **Database & Storage:** PostgreSQL + Supabase + pgvector  
> **Version:** 1.0.0

---

## 📋 Table of Contents
1. [Executive Summary & System Objectives](#1-executive-summary--system-objectives)
2. [Complete Technology Stack](#2-complete-technology-stack)
3. [System Architecture & Layered Pattern](#3-system-architecture--layered-pattern)
4. [Database Schema & Entity Relationship](#4-database-schema--entity-relationship)
   - [Custom Enums](#41-custom-enums)
   - [Core Database Tables](#42-core-database-tables)
   - [Vector Search & pgvector](#43-vector-search--pgvector)
   - [Supabase Storage Buckets](#44-supabase-storage-buckets)
   - [Row Level Security (RLS) Policies](#45-row-level-security-rls-policies)
5. [Authentication, IAM & RBAC System](#5-authentication-iam--rbac-system)
6. [Comprehensive API Reference](#6-comprehensive-api-reference)
   - [6.1 Authentication API (`/api/v1/auth`)](#61-authentication-api-apiv1auth)
   - [6.2 Citizens API (`/api/v1/citizens`)](#62-citizens-api-apiv1citizens)
   - [6.3 Admins & Officials API (`/api/v1/admins`)](#63-admins--officials-api-apiv1admins)
   - [6.4 Complaints API (`/api/v1/complaints`)](#64-complaints-api-apiv1complaints)
   - [6.5 AI Services API (`/api/v1/ai` - Integration)](#65-ai-services-api-apiv1ai---integration)
7. [AI Subsystems & Processing Pipelines](#7-ai-subsystems--processing-pipelines)
8. [Folder Structure & Code Organization](#8-folder-structure--code-organization)
9. [Team Responsibilities & Workflows](#9-team-responsibilities--workflows)
10. [Environment Configuration & Getting Started](#10-environment-configuration--getting-started)

---

## 1. Executive Summary & System Objectives

**MahaTransit AI** is a unified, intelligent, multilingual complaint management platform designed specifically for Mumbai's public transportation network:
- **Mumbai Metro** (Lines 1, 2A, 7, 3 & MMMOCL)
- **BEST Buses** (Brihanmumbai Electric Supply & Transport)
- **Mumbai Suburban Railways** (Central, Western & Harbour lines)

### Core Objectives:
1. **Multilingual Access**: Allow citizens to submit grievances via text or audio voice notes in **Marathi**, **Hindi**, or **English**.
2. **AI-Driven Processing**: Automated Whisper speech-to-text transcription, translation to English, semantic duplicate detection using `pgvector`, and machine learning priority classification via XGBoost.
3. **Automated Ticket Lifecycle**: Automated human-readable ticket number generation (`MT-YYYYMMDD-XXXX`), status workflow progression, official remarks, and citizen feedback ratings.
4. **Role-Based Access Control**: Clean separation between Citizens, Department Officials (BEST / Metro / Railways), and Super Admins.

---

## 2. Complete Technology Stack

| Layer | Component | Tech Choice | Purpose |
|---|---|---|---|
| **API Framework** | REST Framework | **FastAPI** `^0.110.0` | Asynchronous, OpenAPI documented, high-throughput Python API |
| **Server** | ASGI Server | **Uvicorn** `^0.28.0` | High-performance production ASGI runtime |
| **Database** | Relational DB | **PostgreSQL (Supabase)** | Managed PostgreSQL with native RLS and trigger functions |
| **Vector Engine** | Semantic Search | **pgvector** (`vector(384)`) | HNSW index for instant cosine similarity duplicate detection |
| **ORM** | Database ORM | **SQLAlchemy** `^2.0.28` | Python Declarative ORM and connection pooling (`pool_pre_ping`) |
| **Validation** | Data Schemas | **Pydantic v2** `^2.6.4` | Strict type safety, input parsing, serialization (DTOs) |
| **Authentication** | Auth & IAM | **Supabase Auth** `^2.3.0` | Secure email authentication, session management, `auth.users` sync |
| **File Storage** | Object Storage | **Supabase Storage** | Buckets for attachments (`attachments`), voice notes (`voice-files`), avatars |
| **Speech-to-Text** | Audio Processing | **OpenAI Whisper** | Multilingual audio transcription (mr, hi, en) |
| **Translation** | NLP Translation | **NLLB / MarianMT** | Translating Indic languages to English for standardized official review |
| **Duplicate Model** | Embeddings | **Sentence Transformers** | Generating 384-dimensional dense vectors (`all-MiniLM-L6-v2`) |
| **Priority Model** | Classification | **XGBoost** | Tabular/Text ML classifier for Low, Medium, High, and Critical priorities |
| **Client** | Web Frontend | **React + TypeScript + Vite** | Responsive citizen & official dashboards (Tailwind CSS) |

---

## 3. System Architecture & Layered Pattern

The backend strictly follows a decoupled **Layered 3-Tier Architecture** (`Router` ➡️ `Service` ➡️ `Model/Schema`):

```
                       ┌───────────────────────────────────────────────┐
                       │          React + TypeScript Frontend          │
                       └──────────────┬─────────────────▲──────────────┘
                                      │ HTTP REST       │ JSON Response
                                      ▼                 │
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. ROUTER LAYER (`app/api/`)                                                    │
│    - Endpoints: citizens, admins, auth, complaints, ai                          │
│    - Enforces dependencies (get_db, get_current_citizen, require_roles)        │
│    - Delegates all business logic to Service Layer                              │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Calls
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 2. SERVICE LAYER (`app/services/`)                                              │
│    - citizen_service, admin_service, auth_service, complaint_service, ai_service│
│    - Executes transactions, business rules, ticket generation, Supabase calls   │
│    - Formats output data into Pydantic Schemas                                  │
└────────────────────────┬────────────────────────────────┬───────────────────────┘
                         │                                │
         Validates Input │                                │ Queries / Commits
         & Serializes    │                                │
                         ▼                                ▼
┌─────────────────────────────────────────┐  ┌────────────────────────────────────┐
│ 3. SCHEMA LAYER (`app/schemas/`)        │  │ 4. MODEL LAYER (`app/models/`)     │
│    - Pydantic DTOs for Citizens         │  │    - Citizen, Admin, Department    │
│    - Pydantic DTOs for Admins & Auth    │  │    - Complaint, Attachment, Remark │
│    - Pydantic DTOs for Complaints       │  │    - Notification, AIResult        │
└─────────────────────────────────────────┘  └──────────────────┬─────────────────┘
                                                                 │
                                                                 ▼
                                             ┌────────────────────────────────────┐
                                             │ 5. DATABASE & STORAGE (Supabase)   │
                                             │    - PostgreSQL + pgvector (384)   │
                                             │    - Storage Buckets (attachments) │
                                             │    - Supabase Auth (auth.users)    │
                                             └────────────────────────────────────┘
```

---

## 4. Database Schema & Entity Relationship

The database schema is defined in `app/supabase/supabase_schema.sql` and mapped via SQLAlchemy in `app/models/`.

### 4.1 Custom Enums
```sql
CREATE TYPE transit_mode AS ENUM ('metro', 'bus', 'train');
CREATE TYPE complaint_status AS ENUM ('submitted', 'assigned', 'accepted', 'in_progress', 'resolved', 'closed', 'rejected');
CREATE TYPE complaint_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE language_code AS ENUM ('en', 'hi', 'mr');
CREATE TYPE admin_role AS ENUM ('super_admin', 'department_admin', 'complaint_officer');
CREATE TYPE user_type AS ENUM ('citizen', 'admin');
CREATE TYPE attachment_type AS ENUM ('image', 'audio', 'video', 'document');
```

---

### 4.2 Core Database Tables

#### 1. `departments`
Stores transport bodies (Metro, BEST Buses, Local Trains).
- `id` (UUID, Primary Key)
- `name` (VARCHAR 100, UNIQUE)
- `description` (TEXT)
- `is_active` (BOOLEAN, Default: `TRUE`)
- `created_at`, `updated_at` (TIMESTAMPTZ)

#### 2. `complaint_categories`
Hierarchical categories linked to departments.
- `id` (UUID, Primary Key)
- `department_id` (UUID, Foreign Key ➡️ `departments.id` ON DELETE CASCADE)
- `category_name` (VARCHAR 100, NOT NULL)
- `description` (TEXT)
- `is_active` (BOOLEAN, Default: `TRUE`)

#### 3. `citizens`
Citizen profiles linked to Supabase Auth.
- `id` (UUID, Primary Key, Foreign Key ➡️ `auth.users.id` ON DELETE CASCADE)
- `full_name` (VARCHAR 150, NOT NULL)
- `email` (VARCHAR 255, UNIQUE, NOT NULL)
- `phone` (VARCHAR 20)
- `preferred_language` (`language_code`, Default: `'en'`)
- `is_verified` (BOOLEAN, Default: `FALSE`)
- `is_active` (BOOLEAN, Default: `TRUE`)
- `created_at`, `updated_at` (TIMESTAMPTZ)

#### 4. `admins`
Transport officials, department managers, and system administrators.
- `id` (UUID, Primary Key, Foreign Key ➡️ `auth.users.id` ON DELETE CASCADE)
- `department_id` (UUID, Foreign Key ➡️ `departments.id` ON DELETE SET NULL)
- `role` (`admin_role`, Default: `'complaint_officer'`)
- `full_name` (VARCHAR 150, NOT NULL)
- `email` (VARCHAR 255, UNIQUE, NOT NULL)
- `phone` (VARCHAR 20)
- `is_active` (BOOLEAN, Default: `TRUE`)
- `created_at`, `updated_at` (TIMESTAMPTZ)

#### 5. `complaints`
The central grievance entity.
- `id` (UUID, Primary Key)
- `ticket_number` (VARCHAR 30, UNIQUE) — e.g. `MT-20260922-0001`
- `citizen_id` (UUID, Foreign Key ➡️ `citizens.id` ON DELETE CASCADE)
- `department_id` (UUID, Foreign Key ➡️ `departments.id` ON DELETE SET NULL)
- `category_id` (UUID, Foreign Key ➡️ `complaint_categories.id` ON DELETE SET NULL)
- `transit_mode` (`transit_mode`: `'metro'`, `'bus'`, `'train'`)
- `form_data` (JSONB) — Dynamic transport details: route number, bus/train number, coach, stop/station name
- `title` (VARCHAR 255, NOT NULL)
- `description_original` (TEXT, NOT NULL)
- `description_english` (TEXT)
- `language` (`language_code`, Default: `'en'`)
- `priority` (`complaint_priority`, Default: `'medium'`)
- `status` (`complaint_status`, Default: `'submitted'`)
- `embedding` (`vector(384)`) — Semantic embedding for duplicate detection
- `resolved_at`, `closed_at` (TIMESTAMPTZ)
- `feedback_rating` (INT, 1 to 5)
- `feedback_comments` (TEXT)
- `created_at`, `updated_at` (TIMESTAMPTZ)

#### 6. `complaint_attachments`
Evidence files uploaded by citizens or officials.
- `id` (UUID, Primary Key)
- `complaint_id` (UUID, Foreign Key ➡️ `complaints.id` ON DELETE CASCADE)
- `attachment_type` (`attachment_type`: `'image'`, `'audio'`, `'video'`, `'document'`)
- `file_name` (VARCHAR 255)
- `file_url` (TEXT, NOT NULL)
- `mime_type` (VARCHAR 100)
- `file_size` (INT)
- `uploaded_at` (TIMESTAMPTZ)

#### 7. `complaint_remarks`
Audit timeline tracking every status change and official comment.
- `id` (UUID, Primary Key)
- `complaint_id` (UUID, Foreign Key ➡️ `complaints.id` ON DELETE CASCADE)
- `status` (`complaint_status`, NOT NULL)
- `remarks` (TEXT, NOT NULL)
- `updated_by` (UUID, Foreign Key ➡️ `auth.users.id` ON DELETE SET NULL)
- `created_at` (TIMESTAMPTZ)

#### 8. `ai_results`
AI inference metadata per complaint.
- `id` (UUID, Primary Key)
- `complaint_id` (UUID, UNIQUE, Foreign Key ➡️ `complaints.id` ON DELETE CASCADE)
- `speech_text` (TEXT)
- `translated_text` (TEXT)
- `predicted_category_id` (UUID, Foreign Key ➡️ `complaint_categories.id`)
- `category_confidence` (NUMERIC(5,4))
- `predicted_priority` (`complaint_priority`)
- `priority_confidence` (NUMERIC(5,4))
- `processed_at` (TIMESTAMPTZ)

#### 9. `duplicate_complaints`
Stores duplicate pairings detected via vector similarity.
- `id` (UUID, Primary Key)
- `complaint_id` (UUID, Foreign Key ➡️ `complaints.id`)
- `matched_complaint_id` (UUID, Foreign Key ➡️ `complaints.id`)
- `similarity_score` (NUMERIC(5,4))
- `is_duplicate` (BOOLEAN, Default: `TRUE`)
- `created_at` (TIMESTAMPTZ)

#### 10. `notifications`
Real-time user alerts.
- `id` (UUID, Primary Key)
- `user_type` (`user_type`)
- `user_id` (UUID, Foreign Key ➡️ `auth.users.id`)
- `complaint_id` (UUID, Foreign Key ➡️ `complaints.id`)
- `type` (VARCHAR 50)
- `title` (VARCHAR 150)
- `message` (TEXT)
- `is_read` (BOOLEAN, Default: `FALSE`)
- `created_at` (TIMESTAMPTZ)

---

### 4.3 Vector Search & pgvector
The complaints table includes a 384-dimensional vector embedding column indexed via HNSW:
```sql
CREATE INDEX idx_complaints_embedding ON complaints USING hnsw (embedding vector_cosine_ops);
```
Enables sub-millisecond semantic duplicate detection against existing complaints.

---

### 4.4 Supabase Storage Buckets
1. **`profile-images`** *(Public)*: Avatar images for citizens and officials.
2. **`attachments`** *(Public)*: Complaint photos, videos, and document evidence.
3. **`voice-files`** *(Authenticated)*: Citizen voice note audio files.

---

### 4.5 Row Level Security (RLS) Policies
- **Citizens**: Can view/update their own profile (`auth.uid() = id`), view their own complaints (`auth.uid() = citizen_id`), and submit complaints.
- **Department Officers**: Can view and update complaints belonging to their assigned `department_id`.
- **Super Admins**: Full read/write access across all tables.

---

## 5. Authentication, IAM & RBAC System

Authentication uses **Supabase Auth** (`auth.users`) combined with FastAPI dependency injection (`app/api/deps.py`):

```
Client Request (Bearer <token> or X-User-Id)
                  │
                  ▼
         [ FastAPI Dependency ]
                  │
         ┌────────┴────────────────────────┐
         ▼                                 ▼
[ get_current_citizen ]           [ get_current_admin ]
- Validates user in `citizens`    - Validates user in `admins`
- Checks `is_active == True`      - Reads `role` & `department_id`
                                           │
                                           ▼
                                  [ require_roles(...) ]
                                  - super_admin
                                  - department_admin
                                  - complaint_officer
```

### Dependency Resolvers:
- `get_current_citizen`: Injected into citizen-facing endpoints (profile, complaint submission).
- `get_current_admin`: Injected into official-facing endpoints (complaint resolution, officer listing).
- `require_roles(["super_admin", "department_admin"])`: Restricts administrative routes.

---

## 6. Comprehensive API Reference

Base URL Prefix: `/api/v1`

### 6.1 Authentication API (`/api/v1/auth`)

| Method | Route | Access | Request Body | Response Body | Description |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Public | `LoginRequest` | `AuthResponse` | Authenticates citizen or admin credentials via Supabase |
| `POST` | `/api/v1/auth/logout` | Authenticated | None | `MessageResponse` | Signs out active user session |

#### `LoginRequest`
```json
{
  "email": "user@gmail.com",
  "password": "Password123!",
  "user_type": "citizen"
}
```

#### `AuthResponse`
```json
{
  "user_id": "c5dc77ec-3fca-4abb-8d1a-cfcc52b6386d",
  "user_type": "citizen",
  "role": "citizen",
  "full_name": "Aarav Sharma",
  "email": "user@gmail.com",
  "preferred_language": "mr",
  "message": "Citizen login successful"
}
```

---

### 6.2 Citizens API (`/api/v1/citizens`)

| Method | Route | Access | Request Body | Response Body | Description |
|---|---|---|---|---|---|
| `POST` | `/api/v1/citizens/register` | Public | `CitizenRegister` | `CitizenProfileResponse` (201) | Registers citizen in Supabase Auth & creates profile |
| `GET` | `/api/v1/citizens/profile` | Citizen Auth | None | `CitizenProfileResponse` (200) | Retrieves authenticated citizen profile |
| `PUT` | `/api/v1/citizens/profile` | Citizen Auth | `CitizenProfileUpdate` | `CitizenProfileResponse` (200) | Updates name, phone, or preferred language |

#### `CitizenRegister`
```json
{
  "full_name": "Aarav Sharma",
  "email": "aarav@gmail.com",
  "phone": "+919876543210",
  "password": "Password123!",
  "preferred_language": "mr"
}
```

---

### 6.3 Admins & Officials API (`/api/v1/admins`)

| Method | Route | Access | Request Body | Response Body | Description |
|---|---|---|---|---|---|
| `GET` | `/api/v1/admins/profile` | Admin Auth | None | `AdminProfileResponse` (200) | Retrieves official profile & department ID |
| `POST` | `/api/v1/admins/officers` | Super/Dept Admin | `AdminOfficerCreate` | `AdminProfileResponse` (201) | Provisions Department Officer in Supabase Auth |
| `GET` | `/api/v1/admins/officers` | Super/Dept Admin | `?department_id=UUID` | `List[AdminProfileResponse]` (200) | Lists officers filtered by department |

#### `AdminOfficerCreate`
```json
{
  "department_id": "29bfd2c0-da16-4bb5-81f9-622e7e2c70fa",
  "role": "complaint_officer",
  "full_name": "Officer Deshmukh",
  "email": "deshmukh@gmail.com",
  "phone": "+919111111111",
  "password": "OfficerPassword123!"
}
```

---

### 6.4 Complaints API (`/api/v1/complaints`)

| Method | Route | Access | Request Body | Response Body | Description |
|---|---|---|---|---|---|
| `POST` | `/api/v1/complaints` | Public / Citizen | `ComplaintCreate` | `ComplaintResponse` (201) | Creates complaint with ticket number & attachments |
| `GET` | `/api/v1/complaints` | Public / Official | Query Filters | `ComplaintListResponse` (200) | Paginated complaint listing with search & filters |
| `GET` | `/api/v1/complaints/{id}` | Public / Official | None | `ComplaintResponse` (200) | Detailed complaint view with timeline & attachments |
| `PATCH` | `/api/v1/complaints/{id}/status` | Official Auth | `ComplaintRemarkCreate` | `ComplaintResponse` (200) | Updates complaint status & appends timeline remark |
| `POST` | `/api/v1/complaints/{id}/attachments`| Public / Citizen | `ComplaintAttachmentCreate`| `ComplaintAttachmentResponse` (201)| Uploads additional evidence attachment |

#### Query Parameters for `GET /api/v1/complaints`:
- `page`: Page index (default: `1`)
- `limit`: Items per page (default: `20`, max: `100`)
- `status`: `submitted`, `assigned`, `accepted`, `in_progress`, `resolved`, `closed`, `rejected`
- `priority`: `low`, `medium`, `high`, `critical`
- `transit_mode`: `metro`, `bus`, `train`
- `department_id`: Department UUID
- `category_id`: Category UUID
- `citizen_id`: Citizen UUID
- `search`: Keyword search across title, description, and ticket number

---

### 6.5 AI Services API (`/api/v1/ai` - Integration)

| Method | Route | Input | Output | Model Used |
|---|---|---|---|---|
| `POST` | `/api/v1/ai/speech-to-text` | Audio File / URL | `{"text": "...", "language": "mr"}` | OpenAI Whisper |
| `POST` | `/api/v1/ai/translate` | `{"text": "...", "source": "mr"}` | `{"translated_text": "..."}` | NLLB / MarianMT |
| `POST` | `/api/v1/ai/detect-duplicate` | `{"complaint_id": "UUID"}` | `{"is_duplicate": bool, "score": 0.92}` | Sentence Transformers + pgvector |
| `POST` | `/api/v1/ai/predict-priority` | `{"complaint_id": "UUID"}` | `{"priority": "high", "confidence": 0.91}`| XGBoost Classifier |

---

## 7. AI Subsystems & Processing Pipelines

### Complaint Ingestion Pipeline:
```
[ Citizen Voice Note or Multilingual Text ]
                      │
                      ▼
            [ 1. Speech-to-Text ]
        Transcribes audio into Marathi/Hindi/English via Whisper
                      │
                      ▼
             [ 2. Translation ]
      Translates Indic text to English via NLLB/MarianMT
      (Stores description_original + description_english)
                      │
                      ▼
        [ 3. Embedding & Duplicate Detection ]
      Generates 384-dim embedding via Sentence Transformers
      Performs pgvector cosine similarity search (threshold: 0.85)
                      │
                      ▼
          [ 4. Priority Prediction ]
      Classifies priority (Low/Medium/High/Critical) via XGBoost
                      │
                      ▼
         [ 5. Persistence & Notification ]
   Persists complaint to PostgreSQL & creates officer notification
```

---

## 8. Folder Structure & Code Organization

```
MahaTransit_Backend/
├── app/
│   ├── api/                     # Router / Controller Layer
│   │   ├── __init__.py          # Exported API routers
│   │   ├── auth.py              # Auth routes (/api/v1/auth)
│   │   ├── citizens.py          # Citizen routes (/api/v1/citizens)
│   │   ├── admins.py            # Admin/Officer routes (/api/v1/admins)
│   │   ├── complaints.py        # Complaint routes (/api/v1/complaints)
│   │   └── deps.py              # Auth & RBAC dependency guards
│   ├── core/                    # Core Infrastructure
│   │   ├── __init__.py
│   │   ├── config.py            # Application settings (Pydantic Settings)
│   │   └── supabase.py          # Supabase Client singletons
│   ├── db/                      # Database Layer
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy Declarative Base
│   │   └── session.py           # Engine & get_db session generator
│   ├── models/                  # SQLAlchemy ORM Entities
│   │   ├── __init__.py          # Exported ORM models
│   │   ├── citizen.py           # Citizen model
│   │   ├── admin.py             # Admin/Officer model
│   │   └── complaint.py         # Complaint, Department, Category, Attachment, Remark models
│   ├── schemas/                 # Pydantic Validation & Serialization DTOs
│   │   ├── __init__.py          # Exported schemas
│   │   ├── auth.py              # Login & Auth status schemas
│   │   ├── citizen.py           # Citizen register, profile & update schemas
│   │   ├── admin.py             # Admin profile & officer provisioning schemas
│   │   └── complaint.py         # Complaint CRUD, attachment & remark schemas
│   ├── services/                # Business Logic Layer
│   │   ├── __init__.py          # Exported services
│   │   ├── auth_service.py      # Login and logout business logic
│   │   ├── citizen_service.py   # Citizen registration & profile CRUD
│   │   ├── admin_service.py     # Admin profile & officer provisioning logic
│   │   └── complaint_service.py # Complaint lifecycle, ticketing & search logic
│   ├── supabase/
│   │   └── supabase_schema.sql  # Canonical SQL schema with RLS, triggers & pgvector
│   └── main.py                  # FastAPI Application Entrypoint & CORS setup
├── .env.example                 # Environment variables template
├── requirements.txt             # Python package dependencies
└── README.md                    # Project README
```

---

## 9. Team Responsibilities & Workflows

| Team Member | Domain | Scope & Files |
|---|---|---|
| **Member 1** | **Auth, Users, Roles & Profile** | `app/api/citizens.py`, `app/api/admins.py`, `app/api/auth.py`, `app/services/citizen_service.py`, `app/services/admin_service.py`, `app/services/auth_service.py`, `app/models/citizen.py`, `app/models/admin.py`, `app/api/deps.py` |
| **Member 2** | **Complaint System** | `app/api/complaints.py`, `app/services/complaint_service.py`, `app/models/complaint.py`, `app/schemas/complaint.py` |
| **Member 3** | **Dashboards & Analytics** | Officer dashboards, Admin metrics, Department analytics, Status reports |
| **Member 4** | **AI Subsystems** | Speech-to-Text (Whisper), Translation (NLLB), Duplicate Detection (Sentence Transformers), Priority Prediction (XGBoost) |

---

## 10. Environment Configuration & Getting Started

### 10.1 Required `.env` Variables
Create a `.env` file in the root directory:
```env
PROJECT_NAME="MahaTransit AI - Complaint Management System"
API_V1_STR="/api/v1"

# Supabase PostgreSQL Connection URL (from Supabase Dashboard -> Database)
DATABASE_URL="postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres"

# Supabase API Settings (from Supabase Dashboard -> API)
SUPABASE_URL="https://[PROJECT_REF].supabase.co"
SUPABASE_KEY="[ANON_PUBLIC_KEY]"
SUPABASE_SERVICE_ROLE_KEY="[SERVICE_ROLE_SECRET]"
SUPABASE_BUCKET="attachments"
```

### 10.2 Installation & Running Locally
```powershell
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start development server
uvicorn app.main:app --reload --port 8000
```

### 10.3 Interactive Documentation
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---
*MahaTransit AI Backend Engineering Documentation.*
