
CREATE TABLE order_items (
    id            BIGINT        GENERATED ALWAYS AS IDENTITY,
    order_id      BIGINT        NOT NULL,
    product_id    BIGINT        NOT NULL,
    product_name  VARCHAR(150)  NOT NULL,      
    unit_price    NUMERIC(12,2) NOT NULL,      
    quantity      INTEGER       NOT NULL,
    line_total    NUMERIC(14,2) GENERATED ALWAYS AS (unit_price * quantity) STORED,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_order_items           PRIMARY KEY (id),
    CONSTRAINT fk_order_items_order     FOREIGN KEY (order_id)
        REFERENCES orders (id) ON DELETE RESTRICT,
    CONSTRAINT fk_order_items_product   FOREIGN KEY (product_id)
        REFERENCES products (id) ON DELETE RESTRICT,   -- a product that was ever sold can't be deleted (deactivate it)
    CONSTRAINT uq_order_items_order_product UNIQUE (order_id, product_id),  -- merge duplicate products in the app
    CONSTRAINT ck_order_items_price     CHECK (unit_price > 0),   -- BR-01
    CONSTRAINT ck_order_items_quantity  CHECK (quantity > 0)      -- BR-03
);

-- uq_order_items_order_product already indexes (order_id, ...)
CREATE INDEX ix_order_items_product_id ON order_items (product_id);

-- BR-08 / FR-05: items never change after purchase
CREATE TRIGGER trg_order_items_immutable
    BEFORE UPDATE OR DELETE ON order_items
    FOR EACH ROW EXECUTE FUNCTION trg_fn_reject_change();

COMMENT ON TABLE  order_items            IS 'Immutable order lines with price/name snapshot (FR-05, BR-08).';
COMMENT ON COLUMN order_items.unit_price IS 'Price at the moment of purchase, copied from products.price.';
