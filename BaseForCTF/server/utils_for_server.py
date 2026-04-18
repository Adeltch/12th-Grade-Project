__author__ = "Adel Tchernitsky"


import os
import json
from enum import Enum
import threading
from shared.Socket import *
from shared.Shared_Enum import PlayerStatus


QUIZ_FOLDER_DIRECTORY = "Riddles"


class Player:
    def __init__(self, client_sock, status):
        self.socket = client_sock
        self.status = status

        self.ctf = None  # Specific ctf client chooses himself
        self.current_stage_id = None
        self.score = 0
        self.name = ""

        # Track when player started the game
        self.ctf_start_time = None  # TODO: understand what each time counts!
        self.session_start_time = None
        self.total_time = 0  # Will store total time when player finishes

        self.used_hint = False
        self.attempts = 0  # Track wrong attempts for current question

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
        return self.ctf.get_question_by_id(self.current_stage_id)

    def increase_score(self):
        """Add points for current question"""
        self.score += self.get_current_question().points

    def set_ctf(self, ctf):
        self.ctf = ctf
        self.current_stage_id = ctf.questions[0].id

    def move_question(self):
        """Move to the next question if it exists"""
        self.used_hint = False

        next_question = self.ctf.get_next_question_by_id(self.current_stage_id)
        if next_question is not None:
            self.current_stage_id = next_question.id
            return True
        return False

    def __repr__(self):
        return (f"Player name: {self.name}\nCurrent score: {self.score}\nCurrent stage id: {self.current_stage_id}\n"
                f"Current status: {self.status}")


class Question:
    def __init__(self, qid, title, filepath):
        self.id = qid
        self.title = title
        self.filepath = filepath

        self.description = None
        self.flag = None
        self.points = None

        self.category = None
        self.difficulty = None
        self.hint = None

        self.error = False
        self.load_question_data()

    def load_question_data(self):
        """
        reads all data about question from file
        :return: the question, the answer, and points for right answer
        """
        print("Loading question data", self.id)
        try:
            with open(self.filepath, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            print(f"Error: Failed  to load from file {self.filepath}", e)
            self.error = True
            return

        try:
            # Required fields (must exist)
            self.description = data["question"]
            self.flag = data["flag"]
            self.points = data["points"]
        except KeyError as e:
            print(f"Missing key {e} in {self.filepath}")
            self.error = True

        # Optional fields
        self.category = data.get("category", "misc")
        self.difficulty = data.get("difficulty", "unknown")
        self.hint = data.get("hint", None)

    def __repr__(self):
        return (f"Question number: {self.id}, title: {self.title}, Has error occurred while getting question data:"
                f"{self.error}, the question: {self.description}, the flag: {self.flag}, points: {self.points}")


class CTF:
    def __init__(self, ctf_file_path=None):
        if ctf_file_path is None:
            # Default: load first ctf file
            ctf_file_path = os.path.join(QUIZ_FOLDER_DIRECTORY, "CTF1.json")

        with open(ctf_file_path, "r") as f:
            data = json.load(f)

        print(data)
        all_stages = data["Stages"]
        path = data["Path"]
        self.questions = []

        for stage in all_stages:
            stage_path = os.path.normpath(os.path.join(QUIZ_FOLDER_DIRECTORY, path, stage["file"]))
            new_question = Question(stage["id"], stage["title"], stage_path)
            self.questions.append(new_question)

        # Store metadata
        self.category = data.get("category", "misc")
        self.name = os.path.basename(ctf_file_path).split('.')[0]
        print(f"Loaded CTF: {self.name}, {len(self.questions)} stages")

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
    def __init__(self):
        self.players = []
        self.all_ctfs = get_all_ctfs()

        # TODO: leave only one attribute which is ctfs and it's similar to the ctf_map created in get_all_ctfs()
        self.ctf_map = {ctf.name: ctf for ctf in self.all_ctfs}
        self.categories = self._build_categories()

        self.lock = threading.Lock()

    def check_user_name(self, user_name):   # Return true if user_name taken
        with self.lock:
            return any(player.name == user_name and player.name != "" for player in self.players)

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

    def get_ctf_by_name(self, name):
        with self.lock:
            return self.ctf_map.get(name)

    def _build_categories(self):
        categories = {}

        for ctf in self.all_ctfs:
            cat = ctf.category
            if cat not in categories:
                categories[cat] = []

            categories[cat].append(ctf)

        return categories


def get_all_ctfs():
    """
    Scans the Riddles folder for all '.json' CTF files,
    creates a CTF object for each, and returns a map of CTFs.
    """
    # TODO: return a ctf_map here like the one that's currently an object in the LOBBY
    ctfs = []
    for item in os.listdir(QUIZ_FOLDER_DIRECTORY):
        print("Found:", item)
        full_path = os.path.join(QUIZ_FOLDER_DIRECTORY, item)
        print("full path:", full_path)

        # Process only JSON files
        if os.path.isfile(full_path) and item.lower().endswith(".json"):
            try:
                # Load CTF object
                ctf_obj = CTF(ctf_file_path=full_path)
                ctfs.append(ctf_obj)
            except Exception as e:
                print(f"Failed to load CTF from {item}: {e}")

    return ctfs
