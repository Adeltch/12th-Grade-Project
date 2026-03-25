__author__ = "Adel Tchernitsky"


from dataclasses import dataclass


@dataclass
class QuestionMsg:
    """Question server sends to client"""
    question: str
    answers: list
    question_number: int


@dataclass
class Answer:
    """Answer client sends for the question"""
    answer: chr


@dataclass
class Response:
    """Server tells client if he was right or not"""
    is_correct: bool
    question: str
    correct_answer: chr


@dataclass
class LeadersBoard:
    """Leaders board server sends to the client after every question"""
    scores: dict


@dataclass
class FinalScore:
    """Final quiz score the server sends to the client at th end of the game"""
    score: int
