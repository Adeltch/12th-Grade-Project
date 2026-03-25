__author__ = "Adel Tchernitsky"


import threading
import time
import datetime
from ClassUtils import *
import sys
sys.path.append("..")
from Protocol.Socket import *
from Protocol.QuizMessages import *
from Protocol.LobbyMessages import *
from Protocol.RoomMessages import *
from Protocol.ErrorMessages import *
from Utils.Utils import PlayerStatus


BIND_ADDRESS = ("0.0.0.0", 1989)
LISTEN = 5
LF = "\n"
SOCKET_TIMEOUT = 1
SLEEP_TIMEOUT = 0.1
SHOW_RESULT = 4
SHOW_SCORE = 3
SHOW_LEADERS_BOARD_TIMEOUT = 3
ERROR_TIME_OUT = 2
ACCEPT_TIMEOUT = 1


finish = False


def wait_time_out(timeout, start_time=None):
    if start_time is None:
        start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).total_seconds() < timeout:
        time.sleep(SLEEP_TIMEOUT)


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
    player.status = PlayerStatus.InLobby


def handle_choose_room(player, lobby):
    """
    Handle client choosing room he wants to join
    """
    lobby.add_player(player)
    lobby.generate_rooms()

    if not player.send(ShowRooms(lobby.get_rooms_names())):  # Sending client all room options
        finish_player(lobby, player)
        return

    succeeded, response = player.recv()
    if not succeeded or isinstance(response, Exit):  # In case client disconnected forcibly or closed the window
        finish_player(lobby, player)
        return

    if not isinstance(response, ChooseRoom):
        player.send(ProtocolError())  # Send message not by protocol error
        finish_player(lobby, player)  # If got protocol error client will finish
        return

    if response.room_name in lobby:  # Check if room in lobby
        current_room = lobby.get_room(response.room_name)
    else:
        if not player.send(NotExistingRoomError(response.room_name)):
            finish_player(lobby, player)
        wait_time_out(ERROR_TIME_OUT)
        return

    if current_room.status != RoomStatus.Available:  # In case room not available sends client error
        if current_room.status == RoomStatus.Full:  # In case the room is full
            msg = FullRoomError(response.room_name)
        elif current_room.status == RoomStatus.Active:  # In case the room is active
            msg = ActiveRoomError(response.room_name)

        if not player.send(msg):
            finish_player(lobby, player)
        wait_time_out(ERROR_TIME_OUT)
        return

    current_room.add_player(player)  # adds player to players list in the room he chose
    lobby.remove_player(player)  # remove player from lobby, he entered a room

    player.status = PlayerStatus.InRoom
    return lobby.get_room(response.room_name)


def handle_room(player, room):
    """
    Handle all possible client actions in room
    """
    msg = EnterRoom(room.name, player.is_admin, room.quiz.quiz_length,
                    room.quiz.time_to_answer, room.all_players())
    if not player.send(msg):  # Send EnterRoom message
        finish_player(room, player)
        return

    while True:
        player.set_sock_timeout(SOCKET_TIMEOUT)

        try:
            succeeded, request = player.recv()
            if not succeeded:  # In case didn't receive anything and client disconnected forcibly
                finish_player(room, player)
                return
            break
        except SOCKET_TIMEOUT_EXCEPTION:
            if player.status != PlayerStatus.InRoom:
                return
        finally:
            player.set_sock_timeout()

    if isinstance(request, Exit):
        finish_player(room, player)

    elif isinstance(request, StartGame):
        if player.is_admin:  # Player can start game only if he's admin
            room.activate_room()
            for p in room.players:
                if not p.send(GameStarting()):  # In case didn't mange to send message
                    finish_player(room, p)
                else:
                    p.status = PlayerStatus.InGame
        else:
            if not player.send(NotAdminError(room.name)):  # Send player not admin error
                finish_player(room, player)
            wait_time_out(ERROR_TIME_OUT)

    elif isinstance(request, LeaveRoom):
        player.status = PlayerStatus.InLobby
        room.remove_player(player)

    else:
        player.send(ProtocolError())  # Send message not by protocol error
        finish_player(room, player)  # If got protocol error client will finish


def game_loop(player, room):
    """
    Handle a full quiz
    """
    for count, q in enumerate(room.quiz.questions):
        if not player.send(QuestionMsg(q.question, q.get_answers(), count+1)):  # Send client the question
            finish_player(room, player)
            return
        start_time = datetime.datetime.now()

        succeeded, response = player.recv()  # Receive client's answer
        if not succeeded or isinstance(response, Exit):  # In case didn't receive anything or client closed window
            finish_player(room, player)
            return

        if not isinstance(response, Answer):
            player.send(ProtocolError())  # Send message not by protocol error
            finish_player(room, player)  # If got protocol error client will finish
            return

        if response.answer == q.correct:  # Check if response is correct
            is_correct = Response(True, q.question, q.correct)
            player.score += 1
        else:
            is_correct = Response(False, q.question, q.correct)

        wait_time_out(room.quiz.time_to_answer, start_time)  # Waiting for time to answer to finish

        if not player.send(is_correct):  # Sends client the result of current question
            finish_player(room, player)
            return
        wait_time_out(room.quiz.time_to_answer + SHOW_RESULT, start_time)  # Wait for show result

        if not player.send(LeadersBoard(room.get_leaders_board())):  # Sending leaders board after each answer
            finish_player(room, player)
            return
        wait_time_out(SHOW_LEADERS_BOARD_TIMEOUT)  # Wait to finish showing leaders board

    if not player.send(FinalScore(player.score)):  # Send player's final game score
        finish_player(room, player)
        return
    wait_time_out(SHOW_SCORE)  # wait for show score

    player.score = 0
    room.remove_player(player)
    player.status = PlayerStatus.InLobby  # After game player is returned to lobby


def handle_client(player, lobby):
    """
    Handle full client's game until he finishes or global finish is True
    :param player: player object
    :param lobby: lobby object
    """
    room = None
    while player.status != PlayerStatus.Finish and not finish:
        print(f"{player.name} status is: {player.status}")
        if player.status == PlayerStatus.GetUserName:
            handle_get_username(player, lobby)
        elif player.status == PlayerStatus.InLobby:
            room = handle_choose_room(player, lobby)
        elif player.status == PlayerStatus.InRoom:
            handle_room(player, room)
        elif player.status == PlayerStatus.InGame:
            game_loop(player, room)
            lobby.remove_room(room.name)  # Room finished

    finish_player(lobby, player)
    print(f"{player.name} finished")
    close(player.socket)


def main():
    global finish

    lobby = Lobby(get_rooms(), [])  # Create the lobby
    if len(lobby.rooms) == 0:  # If no quizzes can't play
        print("No quizzes found, can't start game without quizzes!")
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
    print("program finished")


if __name__ == "__main__":
    main()
