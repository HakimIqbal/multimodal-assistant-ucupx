-- =====================================================
-- MULTIMODAL ASSISTANT - COMPLETE DATABASE SCHEMA
-- =====================================================
-- File: backend/migrations/complete_schema.sql
-- Description: Complete database schema (AUTH + APP)
-- Version: 1.0.0
-- Last Updated: 2024-06
-- =====================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. AUTHENTICATION & USER MANAGEMENT
-- =====================================================

-- Users
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY, -- Firebase UID
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    avatar_url TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret TEXT,
    backup_codes TEXT[],
    providers TEXT[],
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    ip_addresses TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);
CREATE INDEX IF NOT EXISTS idx_users_providers ON users USING GIN(providers);

-- User Sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

-- Guest Sessions
CREATE TABLE IF NOT EXISTS guest_sessions (
    id VARCHAR(255) PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    chat_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_guest_sessions_token ON guest_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_guest_sessions_expires_at ON guest_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_guest_sessions_is_active ON guest_sessions(is_active);

-- Auth Logs
CREATE TABLE IF NOT EXISTS auth_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    session_type VARCHAR(20) CHECK (session_type IN ('user', 'guest', 'admin')),
    action VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_auth_logs_user_id ON auth_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_logs_action ON auth_logs(action);
CREATE INDEX IF NOT EXISTS idx_auth_logs_success ON auth_logs(success);
CREATE INDEX IF NOT EXISTS idx_auth_logs_created_at ON auth_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_auth_logs_ip_address ON auth_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_auth_logs_metadata ON auth_logs USING GIN(metadata);

-- Rate Limit Logs
CREATE TABLE IF NOT EXISTS rate_limit_logs (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    window_end TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour'),
    is_blocked BOOLEAN DEFAULT FALSE,
    blocked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_ip_address ON rate_limit_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_endpoint ON rate_limit_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_window_start ON rate_limit_logs(window_start);
CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_is_blocked ON rate_limit_logs(is_blocked);

-- IP Blocklist
CREATE TABLE IF NOT EXISTS ip_blocklist (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) UNIQUE NOT NULL,
    reason VARCHAR(255) NOT NULL,
    blocked_until TIMESTAMP WITH TIME ZONE,
    is_permanent BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ip_blocklist_ip_address ON ip_blocklist(ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_blocklist_blocked_until ON ip_blocklist(blocked_until);
CREATE INDEX IF NOT EXISTS idx_ip_blocklist_is_permanent ON ip_blocklist(is_permanent);

-- Two-Factor Backup Codes
CREATE TABLE IF NOT EXISTS two_factor_backup_codes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    code_hash VARCHAR(255) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_2fa_backup_codes_user_id ON two_factor_backup_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_2fa_backup_codes_is_used ON two_factor_backup_codes(is_used);

-- Account Linking
CREATE TABLE IF NOT EXISTS account_links (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('google', 'github')),
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    provider_username VARCHAR(255),
    provider_avatar_url TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
CREATE INDEX IF NOT EXISTS idx_account_links_user_id ON account_links(user_id);
CREATE INDEX IF NOT EXISTS idx_account_links_provider ON account_links(provider);
CREATE INDEX IF NOT EXISTS idx_account_links_provider_user_id ON account_links(provider_user_id);

-- Admin Settings
CREATE TABLE IF NOT EXISTS admin_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_admin_settings_key ON admin_settings(setting_key);

-- =====================================================
-- 2. DOCUMENTS MANAGEMENT
-- =====================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) UNIQUE NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    text_content TEXT,
    file_url TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);

-- =====================================================
-- 3. CHAT LOGS
-- =====================================================

CREATE TABLE IF NOT EXISTS general_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSONB,
    response_time_ms INTEGER,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_general_logs_timestamp ON general_logs(timestamp);

CREATE TABLE IF NOT EXISTS coder_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSONB,
    response_time_ms INTEGER,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_coder_logs_timestamp ON coder_logs(timestamp);

CREATE TABLE IF NOT EXISTS rag_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSONB,
    response_time_ms INTEGER,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_rag_logs_timestamp ON rag_logs(timestamp);

-- =====================================================
-- 4. FEEDBACK SYSTEM
-- =====================================================

CREATE TABLE IF NOT EXISTS chat_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    feature VARCHAR(20) NOT NULL,
    log_id UUID NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chat_feedback_session_id ON chat_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_feedback_log_id ON chat_feedback(log_id);

-- =====================================================
-- 5. ANALYTICS & MONITORING
-- =====================================================

CREATE TABLE IF NOT EXISTS analytics_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature VARCHAR(50) NOT NULL,
    session_id VARCHAR(255),
    user_ip VARCHAR(45),
    action VARCHAR(50),
    model VARCHAR(50),
    extra_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_analytics_log_feature ON analytics_log(feature);
CREATE INDEX IF NOT EXISTS idx_analytics_log_session_id ON analytics_log(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_log_timestamp ON analytics_log(timestamp);

-- =====================================================
-- 6. USER PREFERENCES
-- =====================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'id',
    auto_save BOOLEAN DEFAULT TRUE,
    notifications BOOLEAN DEFAULT TRUE,
    compact_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- =====================================================
-- 7. SNIPPET LIBRARY
-- =====================================================

CREATE TABLE IF NOT EXISTS snippet_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    language VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    code TEXT NOT NULL,
    tags TEXT[],
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_snippet_library_language ON snippet_library(language);
CREATE INDEX IF NOT EXISTS idx_snippet_library_tags ON snippet_library USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_snippet_library_title ON snippet_library(title);

-- =====================================================
-- 8. AUDIT LOGS
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- =====================================================
-- 9. COST TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS cost_budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    budget_type VARCHAR(50) NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cost_budgets_user_id ON cost_budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_cost_budgets_budget_type ON cost_budgets(budget_type);

-- =====================================================
-- 10. WEBHOOK EVENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_webhook_events_webhook_id ON webhook_events(webhook_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_type ON webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(status);

-- =====================================================
-- 10a. WEBHOOK CONFIGS
-- =====================================================

CREATE TABLE IF NOT EXISTS webhook_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    retry_count INTEGER DEFAULT 3,
    timeout INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_webhook_configs_user_id ON webhook_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_webhook_configs_is_active ON webhook_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_webhook_configs_events ON webhook_configs USING GIN(events);

-- =====================================================
-- 11. TRIGGERS & FUNCTIONS (APP)
-- =====================================================

-- Function to update updated_at timestamp (reuse from auth)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_snippet_library_updated_at 
    BEFORE UPDATE ON snippet_library 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean old logs
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM general_logs WHERE timestamp < NOW() - INTERVAL '90 days';
    DELETE FROM coder_logs WHERE timestamp < NOW() - INTERVAL '90 days';
    DELETE FROM rag_logs WHERE timestamp < NOW() - INTERVAL '90 days';
    DELETE FROM analytics_log WHERE timestamp < NOW() - INTERVAL '180 days';
    DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '365 days';
END;
$$ language 'plpgsql';

-- =====================================================
-- 12. VIEWS (APP)
-- =====================================================

-- Chat statistics per feature
CREATE OR REPLACE VIEW chat_statistics AS
SELECT feature, COUNT(*) AS total, AVG(rating) AS avg_rating
FROM chat_feedback
GROUP BY feature;

-- User activity
CREATE OR REPLACE VIEW user_activity AS
SELECT session_id, COUNT(*) AS total_actions, MIN(timestamp) AS first_action, MAX(timestamp) AS last_action
FROM analytics_log
GROUP BY session_id;

-- =====================================================
-- 13. GRANT PERMISSIONS
-- =====================================================

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- =====================================================
-- 14. VERIFICATION
-- =====================================================

-- Check if tables were created successfully
SELECT 
    table_name,
    '✓ Created' as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'users', 'user_sessions', 'guest_sessions', 'auth_logs',
    'rate_limit_logs', 'ip_blocklist', 'two_factor_backup_codes',
    'account_links', 'admin_settings',
    'documents', 'general_logs', 'coder_logs', 'rag_logs',
    'chat_feedback', 'analytics_log', 'user_preferences',
    'snippet_library', 'audit_log', 'cost_budgets', 'webhook_events',
    'webhook_configs'
)
ORDER BY table_name;

-- =====================================================
-- SCHEMA COMPLETE!
-- =====================================================

ALTER TABLE webhook_events
ADD CONSTRAINT fk_webhook_id FOREIGN KEY (webhook_id) REFERENCES webhook_configs(id) ON DELETE CASCADE; 