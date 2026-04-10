__author__ = "Adel Tchernitsky"


from enum import Enum


class PlayerStatus(Enum):
    """Enum of all possible statuses a player can be in"""
    Finish = 0
    GetUserName = 1
    ChooseCTF = 2
    InGame = 3
    ShowResponse = 4
    ShowFinalScore = 5
    ShowError = 9
