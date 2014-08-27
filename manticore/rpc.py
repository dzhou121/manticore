from oslo import messaging

TRANSPORT = None
NOTIFIER = None


def init(conf):
    global TRANSPORT
    TRANSPORT = messaging.get_transport(conf)


def get_client(target, version_cap=None, serializer=None):
    assert TRANSPORT is not None
    return messaging.RPCClient(TRANSPORT,
                               target,
                               version_cap=version_cap,
                               serializer=serializer)


def get_server(target, endpoints, serializer=None):
    assert TRANSPORT is not None
    return messaging.get_rpc_server(TRANSPORT,
                                    target,
                                    endpoints,
                                    executor='eventlet',
                                    serializer=serializer)


def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)
