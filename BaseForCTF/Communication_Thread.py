__author__ = "Adel Tchernitsky"


from Socket import *
from Shared_Enum import PlayerStatus
from Globals import *


SOCKET_TIMEOUT = 1


def handle_message(message):
    """
    Handle message server sent, updates global according to message type
    """
    pass


def create_response():
    """
    Create response that will send to server according to the player status and the input that got from client
    """
    return None


def handle_communication(client_socket):
    set_timeout(client_socket, SOCKET_TIMEOUT)

    while True:
        try:
            succeeded, message = recv(client_socket)
            if not succeeded:  # In case server disconnected everything will finish
                update_global(Globals.status, PlayerStatus.Finish)
                break

            handle_message(message)
        except SOCKET_TIMEOUT_EXCEPTION:
            pass
        except EOFError:
            break

        print(f"current status is: {get_status()}")
        if get_client_input() or get_status() == PlayerStatus.Finish:
            response = create_response()
            if response:
                if not send(client_socket, response):  # In case server disconnected everything will finish
                    update_global(Globals.status, PlayerStatus.Finish)
                    break

            if isinstance(response, Exit):
                break

    close(client_socket)  # Close client socket once finished
