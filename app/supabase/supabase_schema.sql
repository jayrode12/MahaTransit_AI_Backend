-- =============================================================================
-- MahaTransit AI - Comprehensive Supabase Database Schema
-- Project: Intelligent Public Transport Complaint Management System
-- Compatible with Supabase Postgres & Row Level Security (RLS)
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- -----------------------------------------------------------------------------
-- 1. CUSTOM ENUMS
-- -----------------------------------------------------------------------------
CREATE TYPE transit_mode AS ENUM ('metro', 'bus', 'train');
CREATE TYPE complaint_status AS ENUM (
    'submitted', 
    'assigned', 
    'accepted', 
    'in_progress', 
    'resolved', 
    'closed', 
    'rejected'
);
CREATE TYPE complaint_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE language_code AS ENUM ('en', 'hi', 'mr');
CREATE TYPE admin_role AS ENUM ('super_admin', 'department_admin', 'complaint_officer');
CREATE TYPE user_type AS ENUM ('citizen', 'admin');
CREATE TYPE attachment_type AS ENUM ('image', 'audio', 'video', 'document');

-- -----------------------------------------------------------------------------
-- 2. AUTOMATIC UPDATED_AT TRIGGER FUNCTION
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- 3. DEPARTMENTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_departments_updated_at
    BEFORE UPDATE ON departments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- 4. COMPLAINT CATEGORIES TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE complaint_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_complaint_categories_updated_at
    BEFORE UPDATE ON complaint_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- 5. CITIZENS PROFILES TABLE (Linked with Supabase auth.users)
-- -----------------------------------------------------------------------------
CREATE TABLE citizens (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    preferred_language language_code DEFAULT 'en',
        is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_citizens_updated_at
    BEFORE UPDATE ON citizens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- 6. ADMINS / OFFICIALS TABLE (Linked with Supabase auth.users)
-- -----------------------------------------------------------------------------
CREATE TABLE admins (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    role admin_role NOT NULL DEFAULT 'complaint_officer',
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_admins_updated_at
    BEFORE UPDATE ON admins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- 7. COMPLAINTS TABLE (Enhanced with Location, AI Embedding & Feedback)
-- -----------------------------------------------------------------------------
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(30) UNIQUE, -- Auto-generated reference code e.g. MT-20260807-0001
    citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    category_id UUID REFERENCES complaint_categories(id) ON DELETE SET NULL,
    
    -- Transport Mode & Dynamic Form Details
    transit_mode transit_mode NOT NULL,
    form_data JSONB DEFAULT '{}'::jsonb, -- Dynamic transport metadata (e.g., line_or_route_number, station_or_stop_name, vehicle_number)
    
    -- Description & Content
    title VARCHAR(255) NOT NULL,
    description_original TEXT NOT NULL,
    description_english TEXT,
    language language_code DEFAULT 'en',
    
    -- Status & Assignments
    priority complaint_priority DEFAULT 'medium',
    status complaint_status DEFAULT 'submitted',
    
    -- AI Semantic Embedding for Duplicate Detection (384 dim model, e.g. MiniLM-L6-v2)
    embedding vector(384),
    
    -- Resolution & Citizen Feedback
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    feedback_rating INT CHECK (feedback_rating BETWEEN 1 AND 5),
    feedback_comments TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_complaints_updated_at
    BEFORE UPDATE ON complaints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Automatic Ticket Number Generator
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
DECLARE
    seq_num INT;
BEGIN
    SELECT COUNT(*) + 1 INTO seq_num FROM complaints WHERE DATE(created_at) = CURRENT_DATE;
    NEW.ticket_number := 'MT-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(seq_num::text, 4, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_ticket_number
    BEFORE INSERT ON complaints
    FOR EACH ROW EXECUTE FUNCTION generate_ticket_number();

-- -----------------------------------------------------------------------------
-- 8. COMPLAINT ATTACHMENTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE complaint_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID REFERENCES complaints(id) ON DELETE CASCADE,
    attachment_type attachment_type DEFAULT 'image',
    file_name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    mime_type VARCHAR(100),
    file_size INT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 9. COMPLAINT REMARKS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE complaint_remarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID REFERENCES complaints(id) ON DELETE CASCADE,
    status complaint_status NOT NULL,
    remarks TEXT,
    updated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 10. AI RESULTS TABLE (NLP, Voice Speech-to-Text)
-- -----------------------------------------------------------------------------
CREATE TABLE ai_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID REFERENCES complaints(id) ON DELETE CASCADE UNIQUE,
    speech_text TEXT,                          -- Voice audio transcript
    translated_text TEXT,                      -- Machine translation to English
    predicted_category_id UUID REFERENCES complaint_categories(id) ON DELETE SET NULL,
    category_confidence NUMERIC(5, 4),
    predicted_priority complaint_priority,     -- ML predicted priority
    priority_confidence NUMERIC(5, 4),
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 11. DUPLICATE COMPLAINTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE duplicate_complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID REFERENCES complaints(id) ON DELETE CASCADE,
    matched_complaint_id UUID REFERENCES complaints(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5, 4) NOT NULL,
    is_duplicate BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_duplicate_pair UNIQUE (complaint_id, matched_complaint_id)
);

-- -----------------------------------------------------------------------------
-- 12. NOTIFICATIONS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type user_type NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    complaint_id UUID REFERENCES complaints(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 13. AUDIT LOGS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID REFERENCES admins(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- PERFORMANCE INDEXES
-- -----------------------------------------------------------------------------
CREATE INDEX idx_complaints_citizen ON complaints(citizen_id);
CREATE INDEX idx_complaints_department ON complaints(department_id);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_priority ON complaints(priority);
CREATE INDEX idx_complaints_transit_mode ON complaints(transit_mode);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_attachments_complaint ON complaint_attachments(complaint_id);

-- Vector HNSW Index for Fast Cosine Similarity Duplicate Search
CREATE INDEX idx_complaints_embedding ON complaints USING hnsw (embedding vector_cosine_ops);

-- -----------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) POLICIES
-- -----------------------------------------------------------------------------
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE citizens ENABLE ROW LEVEL SECURITY;
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_remarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE duplicate_complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Public/Authenticated read policies for basic lookup data
CREATE POLICY "Public read active departments" ON departments FOR SELECT USING (is_active = TRUE);
CREATE POLICY "Public read active categories" ON complaint_categories FOR SELECT USING (is_active = TRUE);

-- Citizen data access policies
CREATE POLICY "Citizens read own profile" ON citizens FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Citizens update own profile" ON citizens FOR UPDATE USING (auth.uid() = id);

-- Complaints access policies
CREATE POLICY "Citizens read own complaints" ON complaints FOR SELECT USING (auth.uid() = citizen_id);
CREATE POLICY "Citizens insert own complaints" ON complaints FOR INSERT WITH CHECK (auth.uid() = citizen_id);

CREATE POLICY "Admins read department complaints" ON complaints FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM admins 
        WHERE admins.id = auth.uid() 
        AND (admins.role = 'super_admin' OR admins.department_id = complaints.department_id)
    )
);

CREATE POLICY "Admins update department complaints" ON complaints FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM admins 
        WHERE admins.id = auth.uid() 
        AND (admins.role = 'super_admin' OR admins.department_id = complaints.department_id)
    )
);

-- -----------------------------------------------------------------------------
-- SUPABASE STORAGE BUCKETS SETUP (Execute in Supabase SQL Editor)
-- -----------------------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public) VALUES 
('profile-images', 'profile-images', true),
('voice-files', 'voice-files', false),
('attachments', 'attachments', true)
ON CONFLICT (id) DO NOTHING;
