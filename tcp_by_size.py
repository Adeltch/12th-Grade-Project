SIZE_HEADER_FORMAT = "00000000|"  # 8 digits for data size + one delimiter
HEADER_SIZE = len(SIZE_HEADER_FORMAT)


def send_with_size(sock, bdata):
    """
    return true if manged to send
    """
    header_data = str(len(bdata)).zfill(HEADER_SIZE - 1).encode() + b"|"
    full_msg = header_data + bdata

    try:
        sock.send(full_msg)
        return True
    except (ConnectionResetError, ConnectionAbortedError):
        return False


def recv_by_size(sock):
    """
    return True and message if manged to recv
    """
    size_header = b''
    data_len = 0
    while len(size_header) < HEADER_SIZE:  # Receive message length
        try:
            _s = sock.recv(HEADER_SIZE - len(size_header))  # This part isn't pickled
        except (ConnectionResetError, ConnectionAbortedError):
            return False, None

        if _s is None:
            size_header = b''
            break
        size_header += _s

    # Now, the size header field has entirely received in size_header (which is binary).
    data = b''
    if size_header != b'':
        data_len = int(size_header[:HEADER_SIZE - 1])
        while len(data) < data_len:  # Receive the message itself
            try:
                _d = sock.recv(data_len - len(data))
            except (ConnectionResetError, ConnectionAbortedError):
                return False, None

            if _d is None:
                data = b""
                break
            data += _d

    if data_len != len(data):
        data = b""  # Partial data is like no data!
    return True, data
