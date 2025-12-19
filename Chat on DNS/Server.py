__author__ = "Adel Tchernitsky"


from dnslib.server import DNSServer, BaseResolver
from dnslib import RR, QTYPE, A
import base64
import threading
import random


ADDRESS = "0.0.0.0"
PORT = 53
TTL = 60
FINAL_MESSAGE = "end"
MSG_TYPE = "A"


collected_data = []
data_lock = threading.Lock()
write = False


def get_random_response():
    if MSG_TYPE == "A":
        parts = [str(random.randint(0, 256)) for i in range(4)]
        return ".".join(parts)


class SimpleResolver(BaseResolver):
    def resolve(self, request, handler):
        global write
        print("in resolve")
        # Get the full domain name requested
        query_name = request.q.qname
        domain = str(query_name).rstrip(".")

        # Get client's message
        data = domain.replace(".", "")
        print(data)

        if FINAL_MESSAGE in data:
            data = data.replace(FINAL_MESSAGE, "==")
            write = True

        decoded = base64.b64decode(data)
        print(f"Client sent: {decoded}")

        # Store safely
        with data_lock:
            collected_data.append(decoded)

        # Prepare response
        reply = request.reply()
        reply.add_answer(RR(query_name, QTYPE.A, rdata=A(get_random_response()), ttl=TTL))

        return reply


def back_into_file():
    global write
    global collected_data
    
    if not write:
        return

    with data_lock:
        byte_data = b"".join(collected_data)

    with open("new.txt", "wb") as f:
        f.write(byte_data)
    write = False
    collected_data = []



def main():
    print("Starting DNS server on (0.0.0.0:53)")
    server = DNSServer(SimpleResolver(), address=ADDRESS, port=PORT)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    while True:
        try:
            back_into_file()
        except KeyboardInterrupt:
            return


if __name__ == "__main__":
    main()
