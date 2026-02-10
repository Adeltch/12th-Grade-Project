__author__ = "Adel Tchernitsky"


import os
import json
from enum import Enum
from Socket import *
from Shared_Enum import PlayerStatus


QUIZ_FOLDER_DIRECTORY = "Riddles\\"
ALL_STAGES_FILE = "Stages.json"


class Player:
    def __init__(self, client_sock, lobby, status):
        self.socket = client_sock
        self.lobby = lobby
        self.status = status
        self.current_stage_id = 0
        self.score = 0
        self.name = ""

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
    def __init__(self, qid, title, filepath ):
        self.id = qid
        self.title = title
        self.filepath = filepath
        self.description = None
        self.answer = None
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

        self.description = data["question"]
        self.answer = data["answer"]
        self.points = data["points"]

    def __repr__(self):
        return (f"Question number: {self.id}, title: {self.title}, Has error occurred while getting question data:"
                f"{self.error}, the question: {self.description}, the answer: {self.answer}, points: {self.points}")


class CTF:
    def __init__(self):
        all_stages = get_stages()
        print(all_stages)
        self.questions = []
        for stage in all_stages:
            new_question = Question(stage["id"], stage["title"], stage["file"])
            self.questions.append(new_question)
        print(self.questions)


class Lobby:
    def __init__(self, questions, players):
        self.players = players
        self.ctf = questions

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


def get_stages():
    with open(f"{QUIZ_FOLDER_DIRECTORY}{ALL_STAGES_FILE}", "r") as f:
        data = json.load(f)

    all_stages = data["Stages"]
    return all_stages


if __name__ == "__main__":
    main()
