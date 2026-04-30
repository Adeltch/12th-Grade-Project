__author__ = "Adel Tchernitsky"


from shared.Socket import *
from shared.Shared_Enum import PlayerStatus
from shared.Protocol import *
import client.gui as gui


SOCKET_TIMEOUT = 1


status = None


def change_player_status(new_status):
    global status
    status = new_status


def handle_user_name_input():
    return gui.handle_user_name_input()


def handle_ctf_choice(message):
    return gui.handle_ctf_choice(message)


def get_answer(message):
    return gui.get_answer(message)


def handle_show_result(message):
    gui.handle_show_result(message)


def handle_show_final_score(message):
    gui.handle_show_final_score(message)


def handle_show_error(message):
    gui.handle_show_error(message)


OUTPUT_HANDLING = {Response: handle_show_result, FinalScore: handle_show_final_score, GeneralError: handle_show_error}


def show_message_content(message):
    OUTPUT_HANDLING[type(message)](message)


MESSAGE_STATUS_DICT = {GetUserName: PlayerStatus.GetUserName, CTFList: PlayerStatus.ChooseCTF,
                      QuestionMsg: PlayerStatus.InGame, Response: PlayerStatus.ShowResponse,
                      FinalScore: PlayerStatus.ShowFinalScore, GeneralError: PlayerStatus.ShowError}


def handle_message(message):
    if isinstance(message, NameAlreadyTakenError):
        change_player_status(PlayerStatus.GetUserName)
    else:
        for msg_type, status in MESSAGE_STATUS_DICT.items():
            if isinstance(message, msg_type):
                change_player_status(status)
                break

    return create_response(message)


def create_response(message):
    if status == PlayerStatus.Finish:
        return Exit()
    if status == PlayerStatus.GetUserName:
        return Login(handle_user_name_input())
    if status == PlayerStatus.ChooseCTF:
        chosen = handle_ctf_choice(message)
        return CTFChoice(chosen)
    if status == PlayerStatus.InGame:
        current_answer = get_answer(message)
        if current_answer == "hint":
            return HintRequest()
        return Answer(current_answer)
    if status in (PlayerStatus.ShowResponse, PlayerStatus.ShowFinalScore, PlayerStatus.ShowError):
        show_message_content(message)
        if status == PlayerStatus.ShowFinalScore:
            return Exit()


def handle_communication(client_socket):
    global status
    set_timeout(client_socket, SOCKET_TIMEOUT)
    while True:
        try:
            succeeded, message = recv(client_socket)
            if not succeeded:
                change_player_status(PlayerStatus.Finish)
                break
        except SOCKET_TIMEOUT_EXCEPTION:
            pass
        except EOFError:
            break

        response = handle_message(message)
        if response:
            if not send(client_socket, response):
                change_player_status(PlayerStatus.Finish)
                break

        if isinstance(response, Exit):
            break

    close(client_socket)
