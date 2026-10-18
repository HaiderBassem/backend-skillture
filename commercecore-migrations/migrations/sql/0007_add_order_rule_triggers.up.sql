-- Business-rule guards on orders (defense in depth).
-- The app performs the actions; these triggers refuse anything that breaks the BRD.

-- -----------------------------------------------------------------------------
-- 1) Order items must reflect the CURRENT, ACTIVE product at insert time
--    BR-04 (price comes from the system), BR-05 (no inactive products)
-- -----------------------------------------------------------------------------
CREATE FUNCTION trg_fn_order_items_guard_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    p products%ROWTYPE;
BEGIN
    SELECT * INTO p FROM products WHERE id = NEW.product_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'product % does not exist', NEW.product_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    IF NOT p.is_active THEN
        RAISE EXCEPTION 'product % is inactive and cannot be ordered', NEW.product_id
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.unit_price <> p.price THEN
        RAISE EXCEPTION 'unit_price % does not match current product price %', NEW.unit_price, p.price
            USING ERRCODE = 'check_violation';
    END IF;

    IF NEW.product_name <> p.name THEN
        RAISE EXCEPTION 'product_name snapshot does not match current product name'
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_order_items_guard_insert
    BEFORE INSERT ON order_items
    FOR EACH ROW EXECUTE FUNCTION trg_fn_order_items_guard_insert();


-- -----------------------------------------------------------------------------
-- 2) Order updates: only the status may change, only along FR-06 arrows
--    Pending -> Confirmed | Cancelled, decided by an admin (BR-09).
--    A second cancel is rejected, so stock is never restored twice (BR-11).
-- -----------------------------------------------------------------------------
CREATE FUNCTION trg_fn_orders_guard_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.user_id      IS DISTINCT FROM OLD.user_id
    OR NEW.total_amount IS DISTINCT FROM OLD.total_amount
    OR NEW.created_at   IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION 'order %: customer, total and creation time cannot be changed', OLD.id
            USING ERRCODE = 'restrict_violation';
    END IF;

    IF NEW.status IS DISTINCT FROM OLD.status THEN
        IF OLD.status <> 'pending' THEN
            RAISE EXCEPTION 'order % is % and can no longer change status', OLD.id, OLD.status
                USING ERRCODE = 'check_violation';
        END IF;

        IF NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.decided_by AND role = 'admin') THEN
            RAISE EXCEPTION 'order %: status can only be changed by an administrator', OLD.id
                USING ERRCODE = 'insufficient_privilege';
        END IF;

        NEW.decided_at := now();
    ELSIF NEW.decided_by IS DISTINCT FROM OLD.decided_by
       OR NEW.decided_at IS DISTINCT FROM OLD.decided_at THEN
        RAISE EXCEPTION 'order %: decision fields change only together with the status', OLD.id
            USING ERRCODE = 'restrict_violation';
    END IF;

    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_orders_guard_update
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION trg_fn_orders_guard_update();


-- -----------------------------------------------------------------------------
-- 3) Order must be complete when the transaction COMMITS
--    BR-07 (at least one item) + FR-05 (total = Σ unit_price × quantity).
--    DEFERRABLE INITIALLY DEFERRED: the app inserts the order, then its items,
--    in the same transaction; the check runs at COMMIT.
--    Also blocks adding items to an already-placed order (total would mismatch).
-- -----------------------------------------------------------------------------
CREATE FUNCTION trg_fn_orders_check_complete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id  BIGINT;
    v_total     NUMERIC(14,2);
    v_items     INTEGER;
    v_sum       NUMERIC(14,2);
BEGIN
    IF TG_TABLE_NAME = 'orders' THEN
        v_order_id := NEW.id;
    ELSE
        v_order_id := NEW.order_id;
    END IF;

    SELECT total_amount INTO v_total FROM orders WHERE id = v_order_id;

    SELECT count(*), coalesce(sum(line_total), 0)
      INTO v_items, v_sum
      FROM order_items
     WHERE order_id = v_order_id;

    IF v_items = 0 THEN
        RAISE EXCEPTION 'order % must contain at least one item', v_order_id
            USING ERRCODE = 'check_violation';
    END IF;

    IF v_total <> v_sum THEN
        RAISE EXCEPTION 'order % total % does not equal sum of items %', v_order_id, v_total, v_sum
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_orders_check_complete
    AFTER INSERT ON orders
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION trg_fn_orders_check_complete();

CREATE CONSTRAINT TRIGGER trg_order_items_check_complete
    AFTER INSERT ON order_items
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION trg_fn_orders_check_complete();
