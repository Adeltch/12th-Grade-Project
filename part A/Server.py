__author__ = "Adel Tchernitsky"


from dnslib.server import DNSServer, BaseResolver
from dnslib import RR, QTYPE, A, TXT
import base64
import threading
import random
import sys


ADDRESS = "0.0.0.0"
PORT = 53
TTL = 60
RESPONSES_FOLDER = "Response\\"
MSG_TYPE = "A"


collected_data = {}  # {dns_id: bytes}
# TODO: make file object (name, length and content as attributes) then collected_data will be {dns_id: file_object}.
file_length = 0  # expected file size, will be part of object
current_file_name = None
data_lock = threading.Lock()


# Utility Functions
def random_ipv4():
    """Generate a random IPv4 address for A-record responses"""
    return ".".join(str(random.randint(0, 255)) for i in range(4))


def get_random_responses():
    if MSG_TYPE == "A":
        return random_ipv4()


def is_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


# File Handling
def write_file(file_id):
    """Write collected data to disk"""
    file_path = RESPONSES_FOLDER + current_file_name
    with open(file_path, "wb") as f:
        f.write(collected_data[file_id])
    print(f"[+] File written: {file_path}")


def choose_file():
    """Choose output file name"""
    global current_file_name

    if len(sys.argv) > 1:
        arg = sys.argv.pop(1)
        current_file_name = arg
    else:
        current_file_name = "Client.py"

    print(f"[+] Output file: {current_file_name}")


# Client Message Handling
def decode_domain_data(domain_name):
    """
    Extract and base64-decode data hidden in a DNS query name
    """
    raw = domain_name.replace(".", "")
    padded = raw + "=" * (-len(raw) % 4)
    try:
        return base64.b64decode(padded).decode(errors="ignore")
    except Exception as e:
        return f"<decode error: {e}>"


def handle_txt_query():
    """TXT query used as a control message."""
    choose_file()


def handle_a_query(request):
    global file_length

    domain = str(request.q.qname)
    decoded = decode_domain_data(domain)
    print(f"[>] Client sent: {decoded}")

    # First numeric message = file length
    if is_integer(decoded):
        with data_lock:
            file_length = int(decoded)
            print(f"[+] Expected file length: {file_length}")
        return

    with data_lock:
        file_id = request.header.id
        collected_data.setdefault(file_id, b"")
        collected_data[file_id] += decoded.encode()

        if file_length is not None and len(collected_data[file_id]) >= file_length:
            print("[+] File fully received")
            write_file(file_id)


def handle_client_message(request):
    query_type = QTYPE[request.q.qtype]

    if query_type == "TXT":
        handle_txt_query()
    elif query_type == "A":
        handle_a_query(request)


# DNS Response Creation
def create_response(request):
    reply = request.reply()
    query_name = request.q.qname
    query_type = QTYPE[request.q.qtype]

    if query_type == "A":
        reply.add_answer(
            RR(query_name, QTYPE.A, rdata=A(random_ipv4()), ttl=TTL)
        )

    elif query_type == "TXT":
        reply.add_answer(
            RR(query_name, QTYPE.TXT, rdata=TXT(current_file_name), ttl=TTL)
        )

    return reply


# DNS Resolver
class SimpleResolver(BaseResolver):
    def resolve(self, request, handler):
        handle_client_message(request)
        return create_response(request)


# Main
def main():
    print(f"[+] Starting DNS server on {ADDRESS}:{PORT}")
    server = DNSServer(SimpleResolver(), address=ADDRESS, port=PORT)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    while True:
        try:
            continue
        except KeyboardInterrupt:
            print("\n[!] Server shutting down")
            print(collected_data)
            return


if __name__ == "__main__":
    main()
