# MahaTransit AI - Database Structure & Supabase Schema

## Overview
This document outlines the complete database schema for **MahaTransit AI** tailored for **Supabase (PostgreSQL)**, featuring Row-Level Security (RLS), AI vector embedding support (`pgvector`), computer vision detection integration, location coordinates for Leaflet maps, and authentication integration (`auth.users`).

---

## 1. Database Tables

1. **`departments`** `(id, name, description, is_active, created_at, updated_at)`
2. **`complaint_categories`** `(id, department_id, category_name, description, is_active, created_at, updated_at)`
3. **`citizens`** `(id [FK auth.users], full_name, email, phone, preferred_language, is_verified, is_active, created_at, updated_at)`
4. **`admins`** `(id [FK auth.users], department_id, role, full_name, email, phone, is_active, created_at, updated_at)`
5. **`complaints`** `(id, ticket_number, citizen_id, department_id, category_id, transit_mode, form_data (this will be a JSONB object),title, description_original, description_english, language, priority, resolved_at, closed_at, feedback_rating, feedback_comments, created_at, updated_at)`
6. **`complaint_attachments`** `(id, complaint_id, attachment_type, file_name, file_url, mime_type, file_size, uploaded_at)`
7. **`complaint_remarks`** `(id, complaint_id, status, remarks, updated_by, created_at)`
8. **`ai_results`** `(id, complaint_id, speech_text, translated_text, predicted_category_id, category_confidence, predicted_priority, priority_confidence, processed_at)`
9. **`duplicate_complaints`** `(id, complaint_id, matched_complaint_id, similarity_score, is_duplicate, created_at)`
10. **`notifications`** `(id, user_type, user_id, complaint_id, type, title, message, is_read, created_at)`
11. **`audit_logs`** `(id, admin_id, action, table_name, record_id, old_value, new_value, created_at)`

---

## 2. Storage Buckets
- `profile-images` *(Public access)*
- `voice-files` *(Authenticated access only)*
- `attachments` *(Public access)*

---

## 3. Enums
- **`transit_mode`**: `metro`, `bus`, `train`
- **`complaint_status`**: `submitted`, `assigned`, `accepted`, `in_progress`, `resolved`, `closed`, `rejected`
- **`complaint_priority`**: `low`, `medium`, `high`, `critical`
- **`language_code`**: `en`, `hi`, `mr`
- **`admin_role`**: `super_admin`, `department_admin`, `complaint_officer`
- **`user_type`**: `citizen`, `admin`
- **`attachment_type`**: `image`, `audio`, `video`, `document`

---

## 4. Key Supabase Features Included
- **`pgvector` Extension**: Vector embeddings (`vector(384)`) on `complaints` for instant sentence-transformer semantic duplicate search.
- **`HNSW Index`**: Fast vector similarity search index (`idx_complaints_embedding`).
- **Auth Integration**: Primary keys for `citizens` and `admins` reference `auth.users(id)`.
- **Auto Ticket Number Trigger**: Automatically generates human-readable ticket IDs (e.g., `MT-20260807-0001`).
- **Row Level Security (RLS)**: Enforces access control between Citizens and Transport Officials.
- **Location Support**: `latitude` and `longitude` fields to plot complaints on **Leaflet.js / OpenStreetMap**.