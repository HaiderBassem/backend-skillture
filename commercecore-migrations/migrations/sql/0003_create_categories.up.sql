
CREATE TABLE categories (
    id           BIGINT       GENERATED ALWAYS AS IDENTITY,
    name         VARCHAR(100) NOT NULL,
    description  TEXT,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT pk_categories      PRIMARY KEY (id),
    CONSTRAINT ck_categories_name CHECK (btrim(name) <> '')
);

CREATE UNIQUE INDEX uq_categories_name_lower ON categories (lower(name));

CREATE TRIGGER trg_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE categories IS 'Product categories.';
