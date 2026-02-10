__author__ = "Adel Tchernitsky"


import socket
import pickle
import sys
sys.path.append("..\\Protocol")
from tcp_by_size import send_with_size, recv_by_size
from Cipher import AESCipher


SOCKET_TIMEOUT_EXCEPTION = socket.timeout


cipher = AESCipher()


def create():  # Create and return a new socket
    return socket.socket()


def create_server_socket(bind_address, listen):
    """
    Create main socket
    :return: server socket or None in case couldn't create socket
    """
    server_sock = create()
    try:
        server_sock.bind(bind_address)
        server_sock.listen(listen)
        return server_sock
    except OSError:
        return None


def connect(server_address):
    """
    connect the client to server in server_address
    :return: client socket, is_connected
    """
    sock = create()

    try:
        sock.connect(server_address)
        connected = True
    except socket.error:
        connected = False

    return sock, connected


def send(sock, message):  # Send message
    return send_with_size(sock, cipher.encrypt(pickle.dumps(message)))


def recv(sock):  # Receive message
    succeeded, data = recv_by_size(sock)
    if succeeded:
        return succeeded, pickle.loads(cipher.decrypt(data))
    return succeeded, None


def set_timeout(sock, timeout):  # Set timeout for socket
    sock.settimeout(timeout)


def close(sock):  # Close socket
    sock.close()
