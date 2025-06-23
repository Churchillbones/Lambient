from core.container import ServiceContainer


class Dummy:
    pass


def test_register_and_resolve_singleton():
    container = ServiceContainer()
    container.register_singleton(Dummy, Dummy)

    inst1 = container.resolve(Dummy)
    inst2 = container.resolve(Dummy)

    assert isinstance(inst1, Dummy)
    assert inst1 is inst2 