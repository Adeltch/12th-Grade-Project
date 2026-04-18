__author__ = "Adel Tchernitsky"


import threading
import os
from datetime import datetime
from server.utils_for_server import *
from server.db_handler import *
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
        elapsed = (datetime.now() - player.ctf_start_time).total_seconds()
        player.total_time += int(elapsed)  # Records total time

    player.status = PlayerStatus.Finish
    lobby.remove_player(player)

    if player.ctf:
        save_progress(player.name, player.ctf.name, player.current_stage_id, player.score, player.used_hint,
                      player.attempts, player.total_time)


def display_scoreboard(lobby):
    """Prints a live scoreboard of all players on the server console"""
    players = lobby.get_players_snapshot()
    now = datetime.now()

    players = sorted(players, key=lambda p: (
        -p.score,
        p.total_time if p.total_time is not None else (
            int((now - p.game_start_time).total_seconds()) if p.game_start_time else float('inf')
        )
    ))

    print("\n" + "=" * 65)
    print(f"{'PLAYER':15} | {'CTF':15} | {'STAGE':5} | {'SCORE':5} | {'TOTAL TIME':12}")
    print("-" * 65)

    for p in players:
        name = p.name if p.name is not None else ""
        stage = p.current_stage_id if p.current_stage_id is not None else ""
        score = p.score if p.score is not None else 0

        # CTF name (safe access)
        ctf_name = p.ctf.name if getattr(p, "ctf", None) else "No CTF"

        # Total time
        if p.ctf_start_time is None:
            total_str = "Not started"
        else:
            if p.total_time is not None:
                total_elapsed = p.total_time
            else:
                total_elapsed = int((now - p.ctf_start_time).total_seconds())

            total_str = str(total_elapsed)

        print(f"{name:15} | {ctf_name:15} | {stage:5} | {score:5} | {total_str:12}")

    print("=" * 65 + "\n")


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
        # Ensure player exists in DB
        create_player(player.name)

        # Fetch player from db (optional for now)
        # saved_player = get_player(player.name)

        player.status = PlayerStatus.ChooseCTF
        player.session_start_time = datetime.now()
        break


def handle_choose_ctf(player, lobby):
    progress_list = get_all_progress(player.name)
    progress_map = {p["ctf_name"]: p for p in progress_list}

    # Send available CTF names
    categories = {}

    for cat, ctfs in lobby.categories.items():
        categories[cat] = []
        for ctf in ctfs:
            if ctf.name in progress_map:
                prog = progress_map[ctf.name]
                label = f"{ctf.name} (Stage {prog['current_stage_id']}, Score {prog['score']})"
            else:
                label = f"{ctf.name} (new)"
            categories[cat].append(label)

    if not player.send(CTFList(categories)):
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
    update_last_ctf(player.name, selected_ctf.name)

    progress = get_progress(player.name, selected_ctf.name)
    if progress:
        print(f"Resuming {selected_ctf.name} for {player.name}")

        player.current_stage_id = progress["current_stage_id"]
        player.score = progress["score"]
        player.used_hint = progress["used_hint"]
        player.attempts = progress["attempts"]
        player.total_time = progress["total_time"]
    else:
        print(f"Starting new CTF {selected_ctf.name}")
        player.total_time = 0

    player.status = PlayerStatus.InGame
    player.ctf_start_time = datetime.now()
    player.session_start_time = datetime.now()


def handle_question_loop(player, lobby):
    current_question = player.get_current_question()

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
            # TODO: think about keeping hashed flags instead of plain text
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

        # Update time before saving
        elapsed = (datetime.now() - player.session_start_time).total_seconds()
        player.total_time += int(elapsed)
        player.session_start_time = datetime.now()
        # Save progress continuously
        save_progress(player.name, player.ctf.name, player.current_stage_id, player.score, player.used_hint,
                      player.attempts, player.total_time)


def handle_show_final_score(player, lobby):
    player.send(FinalScore(player.score))
    finish_player(lobby, player)


STATE_HANDLERS = {PlayerStatus.GetUserName: handle_get_username, PlayerStatus.ChooseCTF: handle_choose_ctf,
                  PlayerStatus.InGame: handle_question_loop, PlayerStatus.ShowFinalScore: handle_show_final_score}


def handle_client(player, lobby):
    """
    Handle full client's game until he finishes or global finish is True
    :param player: player object
    :param lobby: lobby object
    """
    while player.status != PlayerStatus.Finish:
        print(f"Currently the player: {player}\n")
        handler = STATE_HANDLERS.get(player.status)
        if handler:
            handler(player, lobby)
            if player.status == PlayerStatus.InGame:
                display_scoreboard(lobby)

    finish_player(lobby, player)


def main():
    global finish
    lobby = Lobby()  # Create the initial lobby
    # TODO: update get_questions
    init_db()
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

            player = Player(client_sock, PlayerStatus.GetUserName)  # Create player object for connected client
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
