__author__ = "Adel Tchernitsky"


from Socket import *
import threading
from Utils_for_server import *
from Shared_Enum import PlayerStatus
from Protocol import *


BIND_ADDRESS = ("0.0.0.0", 1989)
LISTEN = 5
ACCEPT_TIMEOUT = 1


finish = False


def finish_player(place, player):
    player.status = PlayerStatus.Finish
    place.remove_player(player)


def handle_get_username(player, lobby):
    """
    Handle receiving user_name from client
    """
    if not player.send(GetUserName()):  # Server asks client to send username
        finish_player(lobby, player)
        return

    succeeded, player_name_msg = player.recv()
    if not succeeded or isinstance(player_name_msg, Exit):  # In case client disconnected forcibly or closed the window
        finish_player(lobby, player)
        return

    if not isinstance(player_name_msg, Login):
        player.send(ProtocolError())  # Send message not by protocol error
        finish_player(lobby, player)  # If got protocol error client will finish
        return

    if lobby.check_user_name(player_name_msg.user_name):    # In case user_name taken
        if not player.send(NameAlreadyTakenError(player_name_msg.user_name)):
            finish_player(lobby, player)
        wait_time_out(ERROR_TIME_OUT)
        return

    player.name = player_name_msg.user_name
    player.status = PlayerStatus.InGame
    print(player)


def handle_question_loop(player):
    pass  # TODO: write this function! This is why client status is'nt changing and the client endlessly asks for name


def handle_client(player, lobby):
    """
    Handle full client's game until he finishes or global finish is True
    :param player: player object
    :param lobby: lobby object
    """
    print(f"current player status {player.status}")
    if player.status == PlayerStatus.Finish:
        finish_player(player, lobby)
    elif player.status == PlayerStatus.GetUserName:
        handle_get_username(player, lobby)
    elif player.status == PlayerStatus.InGame:
        handle_question_loop(player)



def main():
    global finish

    lobby = Lobby(CTF(), [])  # Create the lobby
    # TODO: update get_questions
    if len(lobby.ctf.questions) == 0:  # If no questions can't play
        print("No questions found, can't start CTF without them!")
        return

    server_sock = create_server_socket(BIND_ADDRESS, LISTEN)  # Create server socket
    if not server_sock:
        print("Port already occupied!")
        return
    set_timeout(server_sock, ACCEPT_TIMEOUT)

    threads = []
    while not finish:
        try:
            try:
                client_sock, address = server_sock.accept()
            except SOCKET_TIMEOUT_EXCEPTION:
                continue

            player = Player(client_sock, lobby, PlayerStatus.GetUserName)  # Create player object for connected client
            lobby.players.append(player)  # Adds new player to lobby

            t = threading.Thread(target=handle_client, args=(player, lobby))  # Create new thread for client
            t.start()
            threads.append(t)  # Add thread to threads list

        except KeyboardInterrupt:
            finish = True

    print("Waiting for all players to finish the game...")
    for t in threads:
        t.join()
    print("all threads finished")

    close(server_sock)
    print("Server finished!")


if __name__ == "__main__":
    main()
