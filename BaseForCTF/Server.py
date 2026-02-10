__author__ = "Adel Tchernitsky"


import socket
import threading
from Utils_for_server import *
from Shared_Enum import PlayerStatus


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
    pass


def handle_question_loop(player):
    pass


def handle_client(player, lobby):
    """
    Handle full client's game until he finishes or global finish is True
    :param player: player object
    :param lobby: lobby object
    """
    if player.status is Finish:
        finish_player(player, lobby)
    elif player.status is PlayerStatus.GetUserName:
        handle_get_username(player, lobby)
    elif player.status is PlayerStatus.InGame:
        pass # TODO: finish whatever should be here



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
            except SocketTimeoutException:
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
