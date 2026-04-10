__author__ = "Adel Tchernitsky"


from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GetUserName:
    """Server asks client to send his username"""
    null: int = 0


@dataclass
class Login:
    """Client sends server the username"""
    user_name: str


@dataclass
class CTFList:
    all_ctfs: list[str]


@dataclass
class CTFChoice:
    ctf_name: str


@dataclass
class QuestionMsg:
    """Question server sends to client"""
    question: str
    question_number: int
    hint: Optional[str] = None


@dataclass
class HintRequest:
    """Client asks the server for a hint"""
    null: int = 0


@dataclass
class Answer:
    """Answer client sends for the question"""
    answer: str


@dataclass
class Response:
    """Server tells client if he was right or not"""
    is_correct: bool
    question: str
    points_for_correct_answer: int


@dataclass
class FinalScore:
    """Final quiz score the server sends to the client at th end of the game"""
    score: int


@dataclass
class Exit:
    """In case window was closed by client"""
    null: int = 0


#Error messages
class GeneralError:
    """Error message, message not by protocol"""
    error: str = "Error"


@dataclass
class ProtocolError(GeneralError):
    """Error message, message not by protocol"""
    error: str = "Message not by protocol"


@dataclass
class NameAlreadyTakenError(GeneralError):
    """Error message, name already taken"""
    user_name: str
    error: str = "Name already taken"
