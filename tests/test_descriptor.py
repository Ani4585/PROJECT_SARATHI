from src.container.descriptor import ServiceDescriptor
from src.container.lifetimes import ServiceLifetime


class Logger:
    pass


def test_descriptor():

    descriptor = ServiceDescriptor(
        service_type=Logger,
        implementation_type=Logger,
    )

    assert descriptor.service_type is Logger
    assert descriptor.implementation_type is Logger
    assert descriptor.instance is None
    assert descriptor.lifetime == ServiceLifetime.SINGLETON