__author__ = "Adel Tchernitsky"


from dataclasses import dataclass


@dataclass
class StartGame:
    """Client tells server to start the game"""
    null: int = 0


@dataclass
class GameStarting:
    """Server tells client that the game is starting"""
    null: int = 0


@dataclass
class LeaveRoom:
    """Client wants to leave the room"""
    null: int = 0


@dataclass
class Exit:
    """In case window was closed by client"""
    null: int = 0
