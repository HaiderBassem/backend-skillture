
CREATE TABLE users (
    id             BIGINT       GENERATED ALWAYS AS IDENTITY,
    full_name      VARCHAR(100) NOT NULL,
    email          VARCHAR(255) NOT NULL,
    password_hash  TEXT         NOT NULL,                       -- bcrypt / argon2 hash, never plain text
    role           user_role    NOT NULL DEFAULT 'customer',    -- FR-01: Customer by default
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT pk_users              PRIMARY KEY (id),
    CONSTRAINT ck_users_full_name    CHECK (btrim(full_name) <> ''),
    CONSTRAINT ck_users_email_format CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    CONSTRAINT ck_users_pw_hash      CHECK (password_hash <> '')
);

-- FR-01: no duplicate emails, case-insensitive (Ali@x.com = ali@x.com)
CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email));

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE  users      IS 'Customers and administrators (FR-01). Guests are unauthenticated requests, not rows.';
COMMENT ON COLUMN users.role IS 'Default customer. Admins are promoted manually, never via registration.';
