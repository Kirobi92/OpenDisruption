-- Family Profiles Schema for Kirobi System
-- Zone: WORKSPACE
-- Purpose: User profiles for Sven, Samira, and Sineo with zone-based access control

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'family_member')),
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create zone access permissions table
CREATE TABLE IF NOT EXISTS zone_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    zone VARCHAR(20) NOT NULL CHECK (zone IN ('PUBLIC', 'WORKSPACE', 'FAMILY_PRIVATE', 'QUARANTINE', 'SACRED')),
    can_read BOOLEAN DEFAULT FALSE,
    can_write BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, zone)
);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    language VARCHAR(10) DEFAULT 'de',
    theme VARCHAR(20) DEFAULT 'dark',
    timezone VARCHAR(50) DEFAULT 'Europe/Berlin',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    voice_enabled BOOLEAN DEFAULT FALSE,
    preferred_model VARCHAR(50),
    custom_settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    zone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    attachments JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create file uploads table
CREATE TABLE IF NOT EXISTS file_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    zone VARCHAR(20) NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    zone VARCHAR(20),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_zone_permissions_user_id ON zone_permissions(user_id);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_zone ON conversations(zone);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_file_uploads_user_id ON file_uploads(user_id);
CREATE INDEX idx_file_uploads_zone ON file_uploads(zone);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default family members
-- Note: Passwords should be changed immediately after first login
INSERT INTO users (username, display_name, email, role) VALUES
    ('sven', 'Sven Kirchner', 'sven@kirobi.local', 'admin'),
    ('samira', 'Samira Kirchner', 'samira@kirobi.local', 'family_member'),
    ('sineo', 'Sineo Kirchner', 'sineo@kirobi.local', 'family_member')
ON CONFLICT (username) DO NOTHING;

-- Set up zone permissions for Sven (admin - full access)
INSERT INTO zone_permissions (user_id, zone, can_read, can_write)
SELECT id, 'PUBLIC', true, true FROM users WHERE username = 'sven'
UNION ALL
SELECT id, 'WORKSPACE', true, true FROM users WHERE username = 'sven'
UNION ALL
SELECT id, 'FAMILY_PRIVATE', true, true FROM users WHERE username = 'sven'
UNION ALL
SELECT id, 'QUARANTINE', true, true FROM users WHERE username = 'sven'
UNION ALL
SELECT id, 'SACRED', true, true FROM users WHERE username = 'sven'
ON CONFLICT (user_id, zone) DO NOTHING;

-- Set up zone permissions for Samira (family member - limited access)
INSERT INTO zone_permissions (user_id, zone, can_read, can_write)
SELECT id, 'PUBLIC', true, true FROM users WHERE username = 'samira'
UNION ALL
SELECT id, 'WORKSPACE', true, false FROM users WHERE username = 'samira'
UNION ALL
SELECT id, 'FAMILY_PRIVATE', true, true FROM users WHERE username = 'samira'
ON CONFLICT (user_id, zone) DO NOTHING;

-- Set up zone permissions for Sineo (family member - limited access)
INSERT INTO zone_permissions (user_id, zone, can_read, can_write)
SELECT id, 'PUBLIC', true, true FROM users WHERE username = 'sineo'
UNION ALL
SELECT id, 'WORKSPACE', true, false FROM users WHERE username = 'sineo'
UNION ALL
SELECT id, 'FAMILY_PRIVATE', true, true FROM users WHERE username = 'sineo'
ON CONFLICT (user_id, zone) DO NOTHING;

-- Create default preferences for all family members
INSERT INTO user_preferences (user_id, language, theme, preferred_model)
SELECT id, 'de', 'dark', 'llama3.1:8b' FROM users WHERE username IN ('sven', 'samira', 'sineo')
ON CONFLICT (user_id) DO NOTHING;

COMMENT ON TABLE users IS 'Family member profiles for Kirobi system';
COMMENT ON TABLE zone_permissions IS 'Zone-based access control for family members';
COMMENT ON TABLE conversations IS 'Conversation history isolated per user and zone';
COMMENT ON TABLE messages IS 'Individual messages within conversations';
COMMENT ON TABLE file_uploads IS 'File uploads with zone classification';
COMMENT ON TABLE audit_log IS 'Audit trail for all user actions';
