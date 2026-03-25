__author__ = "Adel Tchernitsky"


from Socket import *


SERVER_ADDRESS = ("127.0.0.1", 1989)
SOCKET_TIMEOUT = 1


def handle_message(message):
    print(f"Server sent> {message}")


def create_response():
    return input(">")


def handle_communication(client_socket):
    # set_timeout(client_socket, SOCKET_TIMEOUT)

    while True:
        try:
            succeeded, message = recv(client_socket)
            if not succeeded:  # In case server disconnected everything will finish
                update_global(Globals.status, PlayerStatus.Finish)
                break

            handle_message(message)
        except SOCKET_TIMEOUT_EXCEPTION:
            pass
        except (EOFError, KeyboardInterrupt):
            break

        response = create_response()
        if response is not None:
            if not send(client_socket, response):  # In case server disconnected everything will finish
                update_global(Globals.status, PlayerStatus.Finish)
                break

    close(client_socket)  # Close client socket once finished


def main():
    client_socket, connected = connect(SERVER_ADDRESS)
    if not connected:
        print(f"Error while trying to connect to {SERVER_ADDRESS}")
        return

    handle_communication(client_socket)


if __name__ == "__main__":
    main()
