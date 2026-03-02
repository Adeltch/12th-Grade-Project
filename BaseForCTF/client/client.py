__author__ = "Adel Tchernitsky"


import threading
from client.communication_thread import handle_communication
from shared.Socket import *

SERVER_ADDRESS = ("127.0.0.1", 1989)


def main():
    client_socket, connected = connect(SERVER_ADDRESS)
    if not connected:
        print(f"Error while trying to connect to {SERVER_ADDRESS}")
        return

    print(f"Connected to Server{SERVER_ADDRESS}")
    handle_communication(client_socket)

    print("Client finished!")


if __name__ == "__main__":
    main()

