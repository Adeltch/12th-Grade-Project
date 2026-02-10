__author__ = "Adel Tchernitsky"


import threading
from Communication_Thread import handle_communication
from Socket import *

SERVER_ADDRESS = ("127.0.0.1", 1989)


def main():
    client_socket, connected = connect(SERVER_ADDRESS)
    if not connected:
        print(f"Error while trying to connect to {SERVER_ADDRESS}")
        return

    print(f"Connected to Server{SERVER_ADDRESS}")

    communication_thread = threading.Thread(target=handle_communication, args=(client_socket,))

    communication_thread.start()

    communication_thread.join()  # Wait for thread to finish

    print("Client finished!")


if __name__ == "__main__":
    main()

