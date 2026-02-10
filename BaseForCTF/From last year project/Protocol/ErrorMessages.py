__author__ = "Adel Tchernitsky"


from dataclasses import dataclass, field


class GeneralError:
    """Error message, message not by protocol"""
    error: str = "Error"


# Generic Error
@dataclass
class ProtocolError(GeneralError):
    """Error message, message not by protocol"""
    error: str = "Message not by protocol"


# Lobby Errors
@dataclass
class NameAlreadyTakenError(GeneralError):
    """Error message, name already taken"""
    user_name: str
    error: str = "Name already taken"


@dataclass
class ActiveRoomError(GeneralError):
    """Error message, client can't join room because game already started"""
    room_name: str
    error: str = "The game started"


@dataclass
class FullRoomError(GeneralError):
    """Error message, client can't join room because it's full"""
    room_name: str
    error: str = "The room is full"


@dataclass
class NotExistingRoomError(GeneralError):
    """Error message, client can't join room because there is no such room in lobby"""
    room_name: str
    error: str = "The room doesn't exist"


# Room Errors
@dataclass
class NotAdminError(GeneralError):
    """Error message, client can't start game because he isn't the admin in the room"""
    room_name: str
    error: str = "You are not the admin"
