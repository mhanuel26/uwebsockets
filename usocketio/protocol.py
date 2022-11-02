"""
Socket.io/Engine.io protocol constructs
"""

PAYLOAD_STRING = const(0)
PAYLOAD_BINARY = const(1)

PACKET_OPEN = const(0)
PACKET_CLOSE = const(1)
PACKET_PING = const(2)
PACKET_PONG = const(3)
PACKET_MESSAGE = const(4)
PACKET_UPGRADE = const(5)
PACKET_NOOP = const(6)

MESSAGE_CONNECT = const(0)
MESSAGE_DISCONNECT = const(1)
MESSAGE_EVENT = const(2)
MESSAGE_ACK = const(3)
MESSAGE_ERROR = const(4)
MESSAGE_BINARY_EVENT = const(5)
MESSAGE_BINARY_ACK = const(6)


def decode_packet(buf):
    if isinstance(buf, str) and buf[0] == 'b':
        # FIXME: implement base64 protocol
        raise NotImplementedError()

    return int(buf[0]), buf[1:]

def decode_payload(buf):
    buf = buf.split(b'\x1e')
    packets = []
    for p in buf:
        p = p.decode('utf-8')
        yield decode_packet(p)
