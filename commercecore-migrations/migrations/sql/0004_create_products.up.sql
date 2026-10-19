-- FR-03  Product management

CREATE TABLE products (
    id              BIGINT        GENERATED ALWAYS AS IDENTITY,
    category_id     BIGINT        NOT NULL,                 -- FR-02: exactly one category
    name            VARCHAR(150)  NOT NULL,
    description     TEXT          NOT NULL DEFAULT '',
    price           NUMERIC(12,2) NOT NULL,                 -- money: NUMERIC, never float
    stock_quantity  INTEGER       NOT NULL DEFAULT 0,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_products          PRIMARY KEY (id),
    -- FR-02: a category that still has products cannot be deleted
    CONSTRAINT fk_products_category FOREIGN KEY (category_id)
        REFERENCES categories (id) ON DELETE RESTRICT,
    CONSTRAINT ck_products_name     CHECK (btrim(name) <> ''),
    CONSTRAINT ck_products_price    CHECK (price > 0),            -- BR-01
    CONSTRAINT ck_products_stock    CHECK (stock_quantity >= 0)   -- BR-02
);

CREATE INDEX ix_products_category_id ON products (category_id);
-- Customers only browse active products: small, fast partial index
CREATE INDEX ix_products_active ON products (category_id, name) WHERE is_active;

CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE  products                IS 'Catalog (FR-03). Deactivate instead of delete.';
COMMENT ON COLUMN products.stock_quantity IS 'Available units. Never negative (BR-02).';
