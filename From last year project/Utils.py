__author__ = "Adel Tchernitsky"


from enum import Enum


class PlayerStatus(Enum):
    """Enum of all possible statuses a player can be in"""
    Finish = 0
    GetUserName = 1
    InLobby = 2
    InRoom = 3
    InGame = 4
    Waiting = 5
    ShowResult = 6
    ShowLeadersBoard = 7
    ShowScore = 8
    ShowError = 9
