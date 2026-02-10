__author__ = "Adel Tchernitsky"


import os
from enum import Enum
import sys
sys.path.append("..")
from Protocol.Socket import *
from Utils.Utils import PlayerStatus


LF = "\n"
SEPARATOR = "."
RIGHT_ANSWER = "(V)"
QUIZ_FOLDER_DIRECTORY = "../Quizzes/"
ROOM_SIZE = 3
AMOUNT_OF_PLAYERS_IN_TOP = 5
MIN_ROOMS_AMOUNT = 5


class Player:
    def __init__(self, client_sock, lobby, status):
        self.socket = client_sock
        self.lobby = lobby
        self.status = status
        self.score = 0
        self.name = ""
        self.is_admin = False

    def send(self, msg):
        if not send(self.socket, msg):
            print(f"{self.name} forcibly closed the connection")
            self.status = PlayerStatus.Finish
            return False

        return True

    def recv(self):
        succeeded, data = recv(self.socket)
        if not succeeded:
            print(f"{self.name} forcibly closed the connection")
            self.status = PlayerStatus.Finish

        return succeeded, data

    def set_sock_timeout(self, timeout=None):
        set_timeout(self.socket, timeout)


class Question:
    def __init__(self, data):
        lines = data.split(LF)
        self.question = lines[0].split(SEPARATOR)[1]
        lines.remove(lines[0])

        self.answers = {}
        for line in lines:
            parts = line.split(SEPARATOR)
            if RIGHT_ANSWER in parts[1]:
                self.correct = parts[0]     # this contains a char between 'a' and 'd', not the whole answer
                parts[1] = parts[1].replace(RIGHT_ANSWER, "")
            self.answers[parts[0]] = parts[1]

    def __repr__(self):
        data = self.question + LF
        for key in self.answers:
            data += key + SEPARATOR + self.answers[key] + LF
        return data + f"The correct answer is {self.correct}"

    def get_answers(self):
        """return list of strings with answers"""
        return [f"{option}.{self.answers[option]}" for option in ['a', 'b', 'c', 'd']]


class Quiz:
    def __init__(self, name, questions, time_to_answer):
        self.name = name
        self.questions = questions
        self.quiz_length = len(questions)
        self.time_to_answer = time_to_answer


class RoomStatus(Enum):
    """Enum for all statuses a room can have"""
    Available = 1
    Full = 2
    Active = 3


class Room:
    def __init__(self, name, quiz):
        self.name = name
        self.quiz = quiz
        self.players = []
        self.status = RoomStatus.Available    # the room could be full, active or good to enter
        self.size = ROOM_SIZE

    def is_empty(self):
        return self.players == []

    def add_player(self, player):
        """Adds player to room if it's available, return True if succeeded and False if didn't"""
        if self.status == RoomStatus.Available:
            player.is_admin = self.is_empty()
            self.players.append(player)
            if len(self.players) == self.size:
                self.status = RoomStatus.Full
            return True

        return False

    def remove_player(self, player):
        """Removes player from room if he is in it"""
        if player in self.players:
            self.players.remove(player)
            self.status = RoomStatus.Available
            if player.is_admin and not self.is_empty():  # In case the admin left someone else should replace him
                self.players[0].is_admin = True

    def check_user_name(self, user_name):  # Return true if a player in room has the specific user_name
        return user_name in [player.name for player in self.players]

    def get_leaders_board(self):
        """Return dictionary of player names and scores that is sorted from highest to lowest score"""
        leaders_board = {player.name: player.score for player in self.players}
        leaders_board = dict(sorted(leaders_board.items(), key=lambda item: item[1], reverse=True))
        return {k: v for i, (k, v) in enumerate(leaders_board.items()) if i < AMOUNT_OF_PLAYERS_IN_TOP}

    def activate_room(self):  # Makes the room active
        self.status = RoomStatus.Active

    def all_players(self):  # Return list of players names
        return [p.name+", is admin" if p.is_admin else p.name for p in self.players]


class Lobby:
    def __init__(self, rooms, players):
        self.rooms = rooms  # list of room objects
        self.players = players

    def get_rooms_names(self):  # Return list of all room names in lobby
        return [room.name for room in self.rooms]

    def __contains__(self, room_name):  # True if room in all rooms of lobby
        return room_name in self.get_rooms_names()

    def get_room(self, room_name):  # Return room object by the room name
        for room in self.rooms:
            if room.name == room_name:
                return room
        return None

    def check_user_name(self, user_name):   # Return true if user_name taken
        if user_name in [player.name for player in self.players]:
            return True

        for r in self.rooms:
            if r.check_user_name(user_name):
                return True

        return False

    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)

    def remove_room(self, room_name):  # Deletes room from lobby only if all players left it (finished playing)
        if len(self.get_room(room_name).players) == 0:
            self.rooms.remove(self.get_room(room_name))

    def generate_rooms(self):  # Refills rooms in lobby
        if len(self.rooms) < MIN_ROOMS_AMOUNT:  # Make sure always more than min rooms amount in lobby
            all_rooms = get_rooms()
            current_rooms_names = [room.name for room in self.rooms]
            for r in all_rooms:
                if r.name not in current_rooms_names:
                    self.rooms.append(r)


def get_time(questions):  # Return time to answer for each question in quizz
    time_to_answer = questions[0]
    questions.remove(time_to_answer)
    return int(time_to_answer.split(": ")[1])
    

def get_questions(file_name):
    """
    reads all questions from the quiz file
    :return: Quiz object
    """
    with open(f"{QUIZ_FOLDER_DIRECTORY}{file_name}", "r") as f:
        data = f.read()

    questions = data.split(2*LF)
    time_to_answer = get_time(questions)
    return Quiz(file_name.split(SEPARATOR)[0], [Question(q) for q in questions], time_to_answer)


def get_rooms():
    """
    read all quizzes and create room for each quiz
    return: list of room objects
    """
    dir_list = os.listdir(QUIZ_FOLDER_DIRECTORY)
    rooms = []
    for file in dir_list:
        room_name = file.split(SEPARATOR)[0]
        rooms.append(Room(room_name, get_questions(file)))

    return rooms
