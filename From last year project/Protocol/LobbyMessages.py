__author__ = "Adel Tchernitsky"


from dataclasses import dataclass


@dataclass
class GetUserName:
    """Server asks client to send his username"""
    null: int = 0


@dataclass
class Login:
    """Client sends server the username"""
    user_name: str


@dataclass
class ShowRooms:
    """Server sends all rooms for client to choose one"""
    room_names: list


@dataclass
class ChooseRoom:
    """Client sends server the room he chose"""
    room_name: str


@dataclass
class EnterRoom:
    """Server accepts client into the room """
    room_name: str
    is_admin: bool
    quiz_length: int
    time_to_answer: int
    players: list
