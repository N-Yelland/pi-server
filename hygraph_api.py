
from typing import Dict, Any

import requests

from datetime import date


CMS_API_URL = "https://api-eu-west-2.hygraph.com/v2/cl2kgfyvs0dme01xrcdjta9z4/master"

AUTH_TOKEN = open("private/auth_token").read()


class BearerToken(requests.auth.AuthBase):
    def __init__(self, token: str):
        self.token = token
    def __call__(self, r: requests.Request):
        r.headers["authorization"] = "Bearer " + self.token
        return r
    

class QueryException(Exception):
    """Exceptions raised when errors occur in queries."""


def query_CMS(query: str) -> Dict[str, Any]:
    payload = {"query": query}
    response = requests.post(
        CMS_API_URL,
        auth=BearerToken(AUTH_TOKEN),
        json=payload
    ).json()

    if "errors" in response:
        error_messages = [error["message"] for error in response["errors"]]
        raise QueryException("\n".join(error_messages))

    return response.get("data")


def parse_quizdle(quizdle: Dict[str, Any]) -> Dict[str, Any]:
    quiz = quizdle.get("quiz")

    clues = []
    words = []
    for i in range(5):
        clue = quiz.get(f"clue{i+1}")
        clues.append(clue)

        word = quiz.get(f"answer{i+1}")
        position_data = quiz.get(f"rowCol{i+1}")
        row, col, direction = position_data.split(",")
        words.append({
            "word": word,
            "row": int(row),
            "col": int(col),
            "direction": direction
        })
    
    return {
        "clues": clues,
        "words": words
    }


def get_quizdles_by_date(date: str):
    query = """{
        quizdles(where: {quiz: {date: "$DATE"} }) {
            quiz {
                clue1, clue2, clue3, clue4, clue5,
                answer1, answer2, answer3, answer4, answer5,
                rowCol1, rowCol2, rowCol3, rowCol4, rowCol5
            }
        }
    }
    """
    query = query.replace("$DATE", date)
    response = query_CMS(query)
    quizdle = response.get("quizdles")[0]
    
    print(quizdle)
    
    return parse_quizdle(quizdle)


if __name__ == "__main__":

    # test_query = """{
    #     quizdles(where: {quiz: {date: "2024-04-10"} } ) {
    #         quiz {
    #             clue1, clue2, clue3, clue4, clue5
    #         }
    #     }
    # }
    # """
    # data = query_CMS(test_query)
    # print(data)

    today = str(date.today())
    print(get_quizdles_by_date(today))