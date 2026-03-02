__author__ = "Adel Tchernitsky"


from enum import Enum
from threading import Lock


my_lock = Lock()
status = None
client_input = None
server_message = None


class Globals(Enum):
    status = 1
    client_input = 2
    server_message = 3


def update_global(global_variable, value):  # Update specific global to be value
    global status
    global client_input
    global server_message

    with my_lock:
        if global_variable == Globals.status:
            status = value
        elif global_variable == Globals.client_input:
            client_input = value
        elif global_variable == Globals.server_message:
            server_message = value


def get_status():  # Return value of the global status
    return status


def get_client_input():  # Return value of the global client_input
    return client_input


def get_server_message():  # Return value of the global server_message
    return server_message
