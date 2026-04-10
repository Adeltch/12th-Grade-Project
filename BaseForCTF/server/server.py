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
MAX_ATTEMPTS_PER_QUESTION = 10


finish = False


def finish_player(lobby, player):
    if player.status != PlayerStatus.Finish:
        player.total_time = datetime.now() - player.game_start_time  # Record total time
    player.status = PlayerStatus.Finish
    lobby.remove_player(player)


def display_scoreboard(lobby):
    """Prints a live scoreboard of all players on the server console"""
    players = lobby.get_players_snapshot()
    players = sorted(players, key=lambda p: (
        -p.score,
        p.total_time if p.total_time else (
            datetime.now() - p.game_start_time if p.game_start_time else datetime.max
        )
    ))

    print("\n" + "=" * 50)
    print(f"{'PLAYER':15} | {'STAGE':5} | {'SCORE':5} | {'TOTAL TIME':12}")
    print("-" * 50)

    for p in players:
        # Total time
        if p.game_start_time is None:
            total_str = "Not started"
        else:
            if p.total_time:
                total_elapsed = p.total_time
            else:
                total_elapsed = datetime.now() - p.game_start_time

            total_str = str(total_elapsed).split('.')[0]

        print(f"{p.name:15} | {p.current_stage_id:5} | {p.score:5} | {total_str:12}")

    print("=" * 50 + "\n")


def handle_get_username(player, lobby):
    """
    Handle receiving user_name from client
    """
    while True:
        # Ask for username
        if not player.send(GetUserName()):
            finish_player(lobby, player)
            return

        succeeded, player_name_msg = player.recv()
        if not succeeded or isinstance(player_name_msg, Exit):
            finish_player(lobby, player)
            return

        if not isinstance(player_name_msg, Login):
            player.send(ProtocolError())
            finish_player(lobby, player)
            return

        # Username already taken
        if lobby.check_user_name(player_name_msg.user_name):
            if not player.send(NameAlreadyTakenError(player_name_msg.user_name)):
                finish_player(lobby, player)
                return
            continue  # Ask for username again

        # Username accepted
        player.name = player_name_msg.user_name
        player.status = PlayerStatus.ChooseCTF
        player.game_start_time = datetime.now()
        break


def handle_choose_ctf(player, lobby):
    # Send available CTF names
    ctf_names = [ctf.name for ctf in lobby.all_ctfs]

    if not player.send(CTFList(ctf_names)):
        finish_player(lobby, player)
        return

    succeeded, msg = player.recv()
    if not succeeded or isinstance(msg, Exit):
        finish_player(lobby, player)
        return

    if not isinstance(msg, CTFChoice):
        player.send(ProtocolError())
        finish_player(lobby, player)
        return

    # Find selected CTF
    selected_ctf = lobby.get_ctf_by_name(msg.ctf_name)

    if not selected_ctf:
        player.send(GeneralError("Invalid CTF choice"))
        return  # let them try again

    # Assign to player
    player.set_ctf(selected_ctf)
    player.status = PlayerStatus.InGame


def handle_question_loop(player, lobby):
    current_question = player.get_current_question()
    print(current_question)

    # Send the question, without hint initially
    if not player.send(QuestionMsg(current_question.description, int(current_question.id), None)):
        finish_player(lobby, player)
        return

    succeeded, player_answer = player.recv()
    if not succeeded or isinstance(player_answer, Exit):
        finish_player(lobby, player)
        return

    # Protocol safety check
    if not isinstance(player_answer, (HintRequest, Answer)):
        # Any message not by protocol
        print(f"Received unexpected message type from {player.name}: {type(player_answer)}")
        player.send(ProtocolError())
        finish_player(lobby, player)
        return

    # Handle hint request
    if isinstance(player_answer, HintRequest):
        player.used_hint = True
        if not player.send(QuestionMsg(current_question.description, int(current_question.id), current_question.hint)):
            finish_player(lobby, player)
        return

    # Handle answer
    if isinstance(player_answer, Answer):
        # Correct answer
        if player_answer.answer.strip().lower() == current_question.flag.strip().lower():
            player_succeeded = True

            # Award points (half if hint was used)
            if player.used_hint:
                player.score += current_question.points // 2
            else:
                player.increase_score()

            # Reset per-question state
            player.used_hint = False
            player.attempts = 0

            # Move to next question or finish
            if not player.move_question():
                player.status = PlayerStatus.ShowFinalScore

        # Wrong answer
        else:
            player_succeeded = False
            player.attempts += 1

            # Too many attempts means skip question
            if player.attempts >= MAX_ATTEMPTS_PER_QUESTION:
                if not player.send(Response(
                        False,
                        f"Too many attempts ({MAX_ATTEMPTS_PER_QUESTION}) for this question. Moving to next challenge.",
                        0
                )):
                    finish_player(lobby, player)
                    return

                player.attempts = 0
                if not player.move_question():
                    player.status = PlayerStatus.ShowFinalScore
                return  # exit after skipping question

        # Send regular response if player hasn't exceeded max attempts
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
        elif player.status == PlayerStatus.ChooseCTF:
            handle_choose_ctf(player, lobby)
        elif player.status == PlayerStatus.InGame:
            handle_question_loop(player, lobby)
            display_scoreboard(lobby)
        elif player.status == PlayerStatus.ShowFinalScore:
            handle_show_final_score(player)


def main():
    global finish
    lobby = Lobby()  # Create the initial lobby
    # TODO: update get_questions
    if len(lobby.all_ctfs) == 0:  # If no questions can't play
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
            lobby.add_player(player)  # Adds new player to lobby

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
