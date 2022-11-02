"""
Micropython Socket.IO client.
"""

import logging
import ure as re
import ujson as json
import usocket as socket
from ucollections import namedtuple
import time

from .protocol import *
from .transport import SocketIO

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

URL_RE = re.compile(r'http://([A-Za-z0-9\-\.]+)(?:\:([0-9]+))?(/.+)?')
URI = namedtuple('URI', ('hostname', 'port', 'path'))

connected = False

def urlparse(uri):
    """Parse http:// URLs"""
    match = URL_RE.match(uri)
    if match:
        return URI(match.group(1), int(match.group(2)), match.group(3))


def _connect_http(hostname, port, path):
    """Stage 1 do the HTTP connection to get our SID"""
    try:
        sock = socket.socket()
        addr = socket.getaddrinfo(hostname, port)
        sock.connect(addr[0][4])

        def send_header(header, *args):
            if __debug__:
                LOGGER.debug(str(header), *args)

            sock.write(header % args + '\r\n')

        send_header(b'GET %s HTTP/1.1', path)
        send_header(b'Host: %s:%s', hostname, port)
        send_header(b'')

        header = sock.readline()[:-2]
        assert header == b'HTTP/1.1 200 OK', header

        length = None

        
        while header:
            header = sock.readline()[:-2]
            if not header:
                break

            header, value = header.split(b': ')
            header = header.lower()
            if __debug__:
                LOGGER.debug("header: %s", repr(header))
            if header == b'content-type':
                if __debug__:
                    LOGGER.debug("value: %s", repr(value))
                assert value == b'text/plain; charset=UTF-8'
            elif header == b'content-length':
                length = int(value)

        assert length

        data = sock.read(length)
        if __debug__: LOGGER.debug("data: %s", repr(data))

        return decode_payload(data)

    finally:
        sock.close()


def connect(uri):
    """Connect to a socket IO server."""
    uri = urlparse(uri)

    assert uri

    path = uri.path or '/' + 'socket.io/?EIO=4'

    # Start a HTTP connection, which will give us an SID to use to upgrade
    # the websockets connection
    packets = _connect_http(uri.hostname, uri.port, path)
    # The first packet should open the connection,
    # following packets might be initialisation messages for us
    
    packet_type, params = next(packets)
    if __debug__:
        print("packet_type, params: ", repr(packet_type), repr(params))

    assert packet_type == PACKET_OPEN
    params = json.loads(params)
    if __debug__: LOGGER.debug("Websocket parameters = %s", params)


    assert 'websocket' in params['upgrades']

    sid = params['sid']
    path += '&sid={}'.format(sid)

    if __debug__:
        LOGGER.debug("Connecting to websocket SID %s", sid)

    # Start a websocket and send a probe on it
    ws_uri = 'ws://{hostname}:{port}{path}&transport=websocket'.format(
        hostname=uri.hostname,
        port=uri.port,
        path=path)

    socketio = SocketIO(ws_uri, **params)

    # handle rest of the packets once we're in the main loop
    @socketio.on('connection')
    def on_connect(data):
        msg = data
        socketio._send_message(MESSAGE_CONNECT, msg)
        packet = socketio._recv()
        if __debug__:
            print("connection recv: ", repr(packet))
        connected = True
        # assert 'sid' in packet
        # for packet_type, data in packets:
        #     socketio._handle_packet(packet_type, data)

    socketio._send_packet(PACKET_PING, 'probe')

    # # Send a follow-up poll
    # _connect_http(uri.hostname, uri.port, path + '&transport=polling')

    # We should receive an answer to our probe
    while True:
        packet = socketio._recv()
        if packet[0] == None:
            time.sleep(0.1)
            continue
        else:
            break
    assert packet == (PACKET_PONG, 'probe')

    # Send a follow-up poll
    _connect_http(uri.hostname, uri.port, path + '&transport=polling')

    # Upgrade the connection
    socketio._send_packet(PACKET_UPGRADE)
    while True:
        packet = socketio._recv()
        if packet[0] == None:
            time.sleep(0.1)
            continue
        else:
            break
    assert packet == (PACKET_NOOP, '')

    return socketio

