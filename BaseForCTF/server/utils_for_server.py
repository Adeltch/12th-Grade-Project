__author__ = "Adel Tchernitsky"


import os
import json
from enum import Enum
import threading
from datetime import datetime
from shared.Socket import *
from shared.Shared_Enum import PlayerStatus


QUIZ_FOLDER_DIRECTORY = "Riddles\\"
FIRST_CTF_FILE = "CTF1.json"


class Player:
    def __init__(self, client_sock, lobby, status):
        self.socket = client_sock
        self.lobby = lobby
        self.status = status
        self.current_stage_id = lobby.get_first_question_id()
        self.score = 0
        self.name = ""
        # Track when player started the game
        self.game_start_time = datetime.now()
        self.total_time = None  # Will store total time when player finishes

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

    def get_current_question(self):
        return self.lobby.ctf.get_question_by_id(self.current_stage_id)

    def increase_score(self):
        """Add points for current question"""
        self.score += self.get_current_question().points

    def move_question(self):
        """Move to the next question if it exists"""
        next_question = self.lobby.ctf.get_next_question_by_id(self.current_stage_id)
        if next_question is not None:
            self.current_stage_id = next_question.id
            return True
        return False

    def __repr__(self):
        return (f"Player name: {self.name}\nCurrent score: {self.score}\nCurrent stage id: {self.current_stage_id}\n"
                f"Current status: {self.status}")


class Question:
    def __init__(self, qid, title, filepath ):
        self.id = qid
        self.title = title
        self.filepath = filepath
        self.description = None
        self.flag = None
        self.points = None

        self.error = False
        self.load_question_data()

    def load_question_data(self):
        """
        reads all data about question from file
        :return: the question, the answer, and points for right answer
        """
        try:
            with open(f"{QUIZ_FOLDER_DIRECTORY}{self.filepath}", "r") as f:
                data = json.load(f)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            print(f"Error: Failed  to load from file {self.filepath}")
            self.error = True
            return

        self.description = data["question"]
        self.flag = data["flag"]
        self.points = data["points"]

    def __repr__(self):
        return (f"Question number: {self.id}, title: {self.title}, Has error occurred while getting question data:"
                f"{self.error}, the question: {self.description}, the flag: {self.flag}, points: {self.points}")


class CTF:
    def __init__(self):
        all_stages, path = get_stages()
        self.questions = []
        for stage in all_stages:
            new_question = Question(stage["id"], stage["title"], os.path.join(path, stage["file"]))
            self.questions.append(new_question)
        print(self.questions)

    def get_question_by_id(self, qid):
        for q in self.questions:
            if q.id == qid:
                return q
        return None

    def get_next_question_by_id(self, qid):
        try:
            index = self.questions.index(self.get_question_by_id(qid))
            return self.questions[index + 1]
        except (ValueError, IndexError):
            return None


class Lobby:
    def __init__(self, questions, players):
        self.players = players
        self.ctf = questions
        self.lock = threading.Lock()

    def check_user_name(self, user_name):   # Return true if user_name taken
        if user_name in [player.name for player in self.players]:
            return True

        return False

    def add_player(self, player):
        with self.lock:
            if player not in self.players:
                self.players.append(player)

    def remove_player(self, player):
        with self.lock:
            if player in self.players:
                self.players.remove(player)

    def get_players_snapshot(self):
        with self.lock:
            return list(self.players)

    def get_first_question_id(self):
        with self.lock:
            return self.ctf.questions[0].id


def get_stages():
    with open(f"{QUIZ_FOLDER_DIRECTORY}{FIRST_CTF_FILE}", "r") as f:
        data = json.load(f)

    all_stages = data["Stages"]
    path = data["Path"]
    return all_stages, path
