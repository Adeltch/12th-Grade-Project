__author__ = "Adel Tchernitsky"


from Socket import *
from Shared_Enum import PlayerStatus
from Globals import *
from Protocol import *


SOCKET_TIMEOUT = 1


status = None


def handle_user_name_input():
    return input("Enter your user name: ")


def get_answer(message):
    return input(f"{message.question_number}. {message.question}\n Your answer: ")


def handle_show_result(message):
    print(f"Your answer was {"correct" if message.is_correct else "incorrect"}\nPoints for this question:"
          f"{message.points_for_correct_answer}")

def handle_show_final_score(message):
    print(f"Your final score: {message.score}")


def handle_show_error(message):
    print(f"Error: {message.error}")


OUTPUT_HENDLING = {Response: handle_show_result, FinalScore: handle_show_final_score, GeneralError: handle_show_error}
def show_message_content(message):
    OUTPUT_HENDLING[type(message)](message)


def handle_message(message):
    """
    Handle message server sent, updates global according to message type
    """
    global status

    if isinstance(message, GetUserName):
        status = PlayerStatus.GetUserName
    elif isinstance(message, QuestionMsg):
        status = PlayerStatus.InGame
    elif isinstance(message, (Response, FinalScore, GeneralError)):
        status = PlayerStatus. ShowData

    return create_response(message)


def create_response(message):
    """
    Create response that will send to server according to the player status and the input that got from client
    """
    if status == PlayerStatus.GetUserName:
        return Login(handle_user_name_input())
    if status == PlayerStatus.Finish:
        return Exit()
    if status == PlayerStatus.InGame:
        return Answer(get_answer(message))
    if status == PlayerStatus.ShowData:
        show_message_content(message)


def handle_communication(client_socket):
    global status
    set_timeout(client_socket, SOCKET_TIMEOUT)

    while True:
        try:
            succeeded, message = recv(client_socket)
            if not succeeded:  # In case server disconnected everything will finish
                status == PlayerStatus.Finish
                break
        except SOCKET_TIMEOUT_EXCEPTION:
            pass
        except EOFError:
            break

        response = handle_message(message)
        print(f"current status is: {get_status()}")
        if response:
            if not send(client_socket, response):  # In case server disconnected everything will finish
                status == PlayerStatus.Finish
                break

        if isinstance(response, Exit):
            break

    close(client_socket)  # Close client socket once finished
