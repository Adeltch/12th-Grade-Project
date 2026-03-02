__author__ = "Adel Tchernitsky"


from enum import Enum


class PlayerStatus(Enum):
    """Enum of all possible statuses a player can be in"""
    Finish = 0
    GetUserName = 1
    InGame = 2
    ShowResponse = 3
    ShowFinalScore = 4
    ShowError = 9
