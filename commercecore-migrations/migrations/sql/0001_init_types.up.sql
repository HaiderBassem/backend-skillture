
CREATE TYPE user_role AS ENUM ('customer', 'admin');


CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'cancelled');

CREATE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

-- Generic "this row is immutable" guard (used by orders / order_items).
CREATE FUNCTION trg_fn_reject_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% on % is not allowed: order history is immutable', TG_OP, TG_TABLE_NAME
        USING ERRCODE = 'restrict_violation';
END;
$$;
