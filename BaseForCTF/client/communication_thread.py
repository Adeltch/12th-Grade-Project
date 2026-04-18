__author__ = "Adel Tchernitsky"


from shared.Socket import *
from shared.Shared_Enum import PlayerStatus
from shared.Protocol import *


SOCKET_TIMEOUT = 1


status = None


def change_player_status(new_status):
    global status
    status = new_status


def handle_user_name_input():
    return input("Enter your user name: ")


def handle_ctf_choice(message):
    print("\nAvailable CTFs:\n")

    index = 1
    flat_list = []
    for category, ctfs in message.categories.items():
        print(f"~~ {category.upper()} ~~")
        for ctf in ctfs:
            # Extract ctf name
            clean_name = ctf.split(" (")[0]

            print(f"{index}. {ctf}")
            flat_list.append((clean_name, ctf))
            index += 1
        print()

    while True:
        try:
            choice = int(input("Choose your CTF -> "))
            return flat_list[choice - 1][0]
        except (ValueError, IndexError):
            print("Invalid choice, try again.")


def get_answer(message):
    text = f"{message.question_number}. {message.question}"
    if message.hint is not None:
        text += f"\nHint: {message.hint}"
    text += "\nYour answer: "
    return input(text)


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


MESSAGE_STATUS_DICT = {GetUserName: PlayerStatus.GetUserName, CTFList: PlayerStatus.ChooseCTF,
                      QuestionMsg: PlayerStatus.InGame, Response: PlayerStatus.ShowResponse,
                      FinalScore: PlayerStatus.ShowFinalScore, GeneralError: PlayerStatus.ShowError}


def handle_message(message):
    """
    Handle message server sent, updates global according to message type
    """
    print(f"MSG TYPE: {type(message)}")

    # Special case
    # TODO: special cases aren't special enough
    if isinstance(message, NameAlreadyTakenError):
        print(f"Username '{message.user_name}' already taken!")
        change_player_status(PlayerStatus.GetUserName)
    else:
        for msg_type, status in MESSAGE_STATUS_DICT.items():
            if isinstance(message, msg_type):
                change_player_status(status)
                break

    return create_response(message)


def create_response(message):
    """
    Create response that will send to server according to the player status and the input that got from client
    """
    #TODO: make funciton shorter
    print(f"\nCurrent status is: {status}")

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
