__author__ = "Adel Tchernitsky"


import threading
import os
from server.utils_for_server import *
from shared.Socket import *
from shared.Protocol import *
from shared.Shared_Enum import PlayerStatus


BIND_ADDRESS = ("0.0.0.0", 1989)
LISTEN = 5
ACCEPT_TIMEOUT = 1


finish = False


def finish_player(lobby, player):
    if player.status != PlayerStatus.Finish:
        # Record total time
        player.total_time = datetime.now() - player.game_start_time
    player.status = PlayerStatus.Finish
    lobby.remove_player(player)


def display_scoreboard(lobby):
    """Prints a live scoreboard of all players on the server console"""
    players = lobby.get_players_snapshot()
    players = sorted(players, key=lambda p: p.score, reverse=True)

    print("\n" + "="*50)
    print(f"{'PLAYER':15} | {'STAGE':5} | {'SCORE':5} | {'TIME ELAPSED'}")
    print("-"*50)

    for p in players:
        stage = p.current_stage_id
        score = p.score

        # If total_time exists (player finished), use it; otherwise calculate running time
        if p.total_time:
            elapsed = p.total_time
        else:
            elapsed = datetime.now() - p.game_start_time

        # Format nicely (remove microseconds)
        elapsed_str = str(elapsed).split('.')[0]

        print(f"{p.name:15} | {stage:5} | {score:5} | {elapsed_str}")
    print("="*50 + "\n")


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


def handle_question_loop(player, lobby):
    current_question = player.get_current_question()

    if not player.send(QuestionMsg(current_question.description, int(current_question.id))):  # Server sends the question
        finish_player(lobby, player)
        return

    succeeded, player_answer = player.recv()
    if not succeeded or isinstance(player_answer, Exit):  # In case client disconnected forcibly or closed the window
        finish_player(lobby, player)
        return

    if not isinstance(player_answer, Answer):
        player.send(ProtocolError())  # Send message not by protocol error
        finish_player(lobby, player)  # If got protocol error client will finish
        return

    if player_answer.answer.strip() == current_question.flag:
        player_succeeded = True
        player.increase_score()
        if not player.move_question():  # In case game finished
            player.status = PlayerStatus.ShowFinalScore

    else:
        player_succeeded = False

    if not player.send(Response(player_succeeded, current_question.description, current_question.points)):
        finish_player(lobby, player)
        return


def handle_show_final_score(player):
    player.send(FinalScore(player.score))
    player.status = PlayerStatus.Finish


def handle_client(player, lobby):
    """
    Handle full client's game until he finishes or global finish is True
    :param player: player object
    :param lobby: lobby object
    """
    while True:
        print(f"Currently the player: {player}\n")
        if player.status == PlayerStatus.Finish:
            finish_player(lobby, player)
            break
        elif player.status == PlayerStatus.GetUserName:
            handle_get_username(player, lobby)
        elif player.status == PlayerStatus.InGame:
            handle_question_loop(player, lobby)
            display_scoreboard(lobby)
        elif player.status == PlayerStatus.ShowFinalScore:
            handle_show_final_score(player)


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
