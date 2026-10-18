
DROP TRIGGER IF EXISTS trg_order_items_check_complete ON order_items;
DROP TRIGGER IF EXISTS trg_orders_check_complete      ON orders;
DROP FUNCTION IF EXISTS trg_fn_orders_check_complete();

DROP TRIGGER IF EXISTS trg_orders_guard_update ON orders;
DROP FUNCTION IF EXISTS trg_fn_orders_guard_update();

DROP TRIGGER IF EXISTS trg_order_items_guard_insert ON order_items;
DROP FUNCTION IF EXISTS trg_fn_order_items_guard_insert();
