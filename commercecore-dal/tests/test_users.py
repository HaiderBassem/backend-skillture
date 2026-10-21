"""Users: the optional international_id (migration 0008)."""


def test_international_id_defaults_to_zero(new_uow):
    with new_uow() as uow:
        user = uow.users.add("Alice Customer", "alice@example.com", "hash-1")
    assert user.international_id == 0


def test_international_id_is_stored_and_read_back(new_uow):
    with new_uow() as uow:
        added = uow.users.add("Bob Customer", "bob@example.com", "hash-2", international_id=9876543210)
    with new_uow() as uow:
        assert uow.users.get_by_email("bob@example.com").international_id == 9876543210
        assert uow.users.get_by_id(added.id).international_id == 9876543210
