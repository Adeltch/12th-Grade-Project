__author__ = "Adel Tchernitsky"


from Socket import *
from Shared_Enum import PlayerStatus
from Globals import *
from Protocol import *


SOCKET_TIMEOUT = 1


status = None


def change_player_status(new_status):
    global status
    status = new_status


def handle_user_name_input():
    return input("Enter your user name: ")


def get_answer(message):
    return input(f"{message.question_number}. {message.question}\n Your answer: ")


def handle_show_result(message):
    print(f"\nYour answer was {'correct' if message.is_correct else 'incorrect'}\n"
          f"Points for this question: {message.points_for_correct_answer}")


def handle_show_final_score(message):
    print(f"\nYour final score: {message.score}")


def handle_show_error(message):
    print(f"\nError: {message.error}")


OUTPUT_HANDLING = {Response: handle_show_result, FinalScore: handle_show_final_score, GeneralError: handle_show_error}


def show_message_content(message):
    OUTPUT_HANDLING[type(message)](message)


def handle_message(message):
    """
    Handle message server sent, updates global according to message type
    """
    print(f"MSG TYPE: {type(message)}")
    if isinstance(message, GetUserName):
        change_player_status(PlayerStatus.GetUserName)
    elif isinstance(message, QuestionMsg):
        change_player_status(PlayerStatus.InGame)
    elif isinstance(message, Response):
        change_player_status(PlayerStatus.ShowResponse)
    elif isinstance(message, FinalScore):
        change_player_status(PlayerStatus.ShowFinalScore)
    elif isinstance(message, GeneralError):
        change_player_status(PlayerStatus.ShowError)

    return create_response(message)


def create_response(message):
    """
    Create response that will send to server according to the player status and the input that got from client
    """
    print(f"\nCurrent status is: {status}")
    if status == PlayerStatus.Finish:
        return Exit()
    if status == PlayerStatus.GetUserName:
        return Login(handle_user_name_input())
    if status == PlayerStatus.InGame:
        return Answer(get_answer(message))
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
            if not succeeded:  # In case server disconnected everything will finish
                change_player_status(PlayerStatus.Finish)
                break
        except SOCKET_TIMEOUT_EXCEPTION:
            pass
        except EOFError:
            break

        response = handle_message(message)
        print(f"\nResponse is: {response}")
        if response:
            if not send(client_socket, response):  # In case server disconnected everything will finish
                change_player_status(PlayerStatus.Finish)
                break

        if isinstance(response, Exit):
            break

    close(client_socket)  # Close client socket once finished
    print("Client finished")
