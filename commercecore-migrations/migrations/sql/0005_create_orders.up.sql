
CREATE TABLE orders (
    id            BIGINT        GENERATED ALWAYS AS IDENTITY,
    user_id       BIGINT        NOT NULL,                     -- FR-05: one customer
    status        order_status  NOT NULL DEFAULT 'pending',   -- FR-04 step 10
    total_amount  NUMERIC(14,2) NOT NULL,                     -- FR-04 step 6
    decided_by    BIGINT,                                     -- admin who confirmed/cancelled
    decided_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_orders            PRIMARY KEY (id),
    CONSTRAINT fk_orders_user       FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_orders_decided_by FOREIGN KEY (decided_by)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT ck_orders_total      CHECK (total_amount > 0),
    -- Pending  <=> no decision yet.  Confirmed / Cancelled <=> decision recorded.
    CONSTRAINT ck_orders_decision   CHECK (
        (status = 'pending'  AND decided_at IS NULL     AND decided_by IS NULL)
     OR (status <> 'pending' AND decided_at IS NOT NULL AND decided_by IS NOT NULL)
    )
);

-- FR-07: "my orders, newest first"
CREATE INDEX ix_orders_user_created   ON orders (user_id, created_at DESC);
-- Admin: "all pending orders"
CREATE INDEX ix_orders_status_created ON orders (status, created_at DESC);
CREATE INDEX ix_orders_decided_by     ON orders (decided_by) WHERE decided_by IS NOT NULL;

-- Orders are history: never deleted (FR-05)
CREATE TRIGGER trg_orders_no_delete
    BEFORE DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION trg_fn_reject_change();

COMMENT ON TABLE  orders            IS 'Customer orders (FR-04..FR-07). Never deleted.';
COMMENT ON COLUMN orders.decided_by IS 'Admin who confirmed or cancelled the order.';
