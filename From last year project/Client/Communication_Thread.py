__author__ = "Adel Tchernitsky"


from Globals import Globals, update_global, get_client_input, get_status
import sys
sys.path.append("..")
from Protocol.Socket import *
from Protocol.QuizMessages import *
from Protocol.LobbyMessages import *
from Protocol.RoomMessages import *
from Protocol.ErrorMessages import *
from Utils.Utils import PlayerStatus


SOCKET_TIMEOUT = 1


def handle_message(message):
    """
    Handle message server sent, updates global according to message type
    """
    if isinstance(message, GetUserName):
        update_global(Globals.status, PlayerStatus.GetUserName)

    if isinstance(message, ShowRooms):
        update_global(Globals.status, PlayerStatus.InLobby)
        update_global(Globals.server_message, message.room_names)

    elif isinstance(message, EnterRoom):
        update_global(Globals.status, PlayerStatus.InRoom)
        update_global(Globals.server_message, message)

    elif isinstance(message, GameStarting):
        update_global(Globals.status, PlayerStatus.InGame)

    elif isinstance(message, QuestionMsg):
        update_global(Globals.status, PlayerStatus.InGame)
        update_global(Globals.server_message, message)

    elif isinstance(message, Response):
        update_global(Globals.status, PlayerStatus.ShowResult)
        update_global(Globals.server_message, message)

    elif isinstance(message, LeadersBoard):
        update_global(Globals.status, PlayerStatus.ShowLeadersBoard)
        update_global(Globals.server_message, message.scores)

    elif isinstance(message, FinalScore):
        update_global(Globals.status, PlayerStatus.ShowScore)
        update_global(Globals.server_message, message.score)

    elif isinstance(message, GeneralError):
        update_global(Globals.server_message, message.error)
        update_global(Globals.status, PlayerStatus.ShowError)


def create_response():
    """
    Create response that will send to server according to the player status and the input that got from client
    """
    response = None
    if get_status() == PlayerStatus.GetUserName:
        user_name = get_client_input()
        response = Login(user_name)

    elif get_status() == PlayerStatus.InLobby:
        room_name = get_client_input()
        response = ChooseRoom(room_name)

    elif get_status() == PlayerStatus.InRoom and get_client_input() == "start":
        response = StartGame()

    elif get_status() == PlayerStatus.InRoom and get_client_input() == "back":
        response = LeaveRoom()

    elif get_status() == PlayerStatus.InGame:
        answer = get_client_input()
        response = Answer(answer)
        update_global(Globals.status, PlayerStatus.Waiting)  # After answer should see wait for all to answer screen

    elif get_status() == PlayerStatus.Finish:
        response = Exit()

    if response:
        update_global(Globals.client_input, None)

    return response


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
