
from typing import Dict, Any, List

import requests
import json

from datetime import date, timedelta
from random import randint

from authentication import authetnicate, AuthenticationError

CMS_API_URL = "https://api-eu-west-2.hygraph.com/v2/cl2kgfyvs0dme01xrcdjta9z4/master"

AUTH_TOKEN = open("private/auth_token").read()

# Date of the First Quizdle
START_DATE = "2022-05-08"


class BearerToken(requests.auth.AuthBase):
    def __init__(self, token: str):
        self.token = token
    def __call__(self, r: requests.Request):
        r.headers["authorization"] = "Bearer " + self.token
        return r
    

class QueryException(Exception):
    """Exceptions raised when errors occur in queries."""


def query_CMS(query: str, **variables) -> Dict[str, Any]:
    payload = {"query": query, "variables": variables}

    response = requests.post(
        CMS_API_URL,
        auth=BearerToken(AUTH_TOKEN),
        json=payload,
        headers={"gcms-stage": "PUBLISHED"}
    ).json()

    if "errors" in response:
        error_messages = [error["message"] for error in response["errors"]]
        raise QueryException("\n".join(error_messages))

    return response.get("data")


def parse_quizdle(quizdle: Dict[str, Any]) -> Dict[str, Any]:
    quiz = quizdle.get("quiz")

    clues = []
    for i in range(5):
        clue = quiz.get(f"clue{i+1}")
        word = quiz.get(f"answer{i+1}")
        position_data = quiz.get(f"rowCol{i+1}")
        row, col, direction = position_data.split(",")
        clues.append({
            "clue": clue,
            "word": word,
            "row": int(row),
            "col": int(col),
            "direction": direction
        })
    
    return {
        "clues": clues,
    }


def get_quizdle_by_date(date: str):
    query = """query FetchTodaysQuizdle {
        quizdles(where: {quiz: {date: "$DATE"} }) {
            quiz {
                clue1, clue2, clue3, clue4, clue5,
                answer1, answer2, answer3, answer4, answer5,
                rowCol1, rowCol2, rowCol3, rowCol4, rowCol5
            }
        }
    }
    """

    # TODO: replace this with a GraphQL variable
    query = query.replace("$DATE", date)
    response = query_CMS(query)
    quizdles = response.get("quizdles")
    
    if not quizdles:
        return
    
    quizdle = quizdles[0]    
    return parse_quizdle(quizdle)


def get_random_quizdle():
    
    start_date = date.fromisoformat(START_DATE)
    max_diff = (date.today() - start_date).days - 1
        
    random_quizdle = None
    while random_quizdle is None:
        diff = randint(0, max_diff)
        random_date = str(start_date + timedelta(days=diff))
        random_quizdle = get_quizdle_by_date(random_date)
    
    print(f"Quizlde #{diff} ({random_date})")
    return random_quizdle


def get_week_status(start_date: str) -> List[str]:
    # Returns the dates that have quizdle for those in the next week after and including start_date.
    query = """query GetQuizdlesBetween($start_date: Date, $end_date: Date) {
        quizdles(where: {quiz: {date_gte: $start_date, date_lte: $end_date}}) {
            quiz {
                date
            }
        }
    }
    """
    end_date = str(date.fromisoformat(start_date) + timedelta(days=7))
    response = query_CMS(query, start_date=start_date, end_date=end_date)
    dates = [quizdle["quiz"]["date"] for quizdle in response["quizdles"]]
    return dates


def write_new_quizdle(quizdle: Dict[str, Any]) -> Dict[str, Any]:
    create_query = """mutation createNewQuizdle($data: QuizdleCreateInput!) {
        createQuizdle(data: $data) {
            id
            quiz {
                id
            }
        }
    }
    """
    publish_query = """mutation publishExistingQuizdle($id: ID!) {
        publishQuizdle(where: {id: $id}) {
            id
        }
    }"""

    response = query_CMS(create_query, data={"quiz": {"create": quizdle}})

    quizlde_id = response["createQuizdle"]["id"]

    response = query_CMS(publish_query, id=quizlde_id)

    return {"success": True}



def perform_query(query_type: str, **kwargs) -> Any:
    match query_type:
        case "get_week_status":
            return get_week_status(**kwargs)
        
        case "write_new_quizdle":
            authetnicate(kwargs.get("password"), "private/quizdle_verifier")
            
            quizdle = json.loads(kwargs.get("quizdle"))
            return write_new_quizdle(quizdle)


# Room for doing some testing...
if __name__ == "__main__":

    print(get_week_status("2024-05-16"))