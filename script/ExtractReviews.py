import logging
import time
from typing import Dict, List
import os
import requests
import json
from datetime import datetime, timedelta

GPLAY_BASE_URL = 'https://gplayapi.cashlessconsumer.in'

def get_reviews(app_id, next_pagination_token=None):
    url = f"{GPLAY_BASE_URL}/api/apps/{app_id}/reviews?num=100"
    params = {"nextPaginationToken": next_pagination_token} if next_pagination_token else {}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

def get_appinfo(app_id):
    url = f"{GPLAY_BASE_URL}/api/apps/{app_id}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def get_permissions(app_id):
    url = f"{GPLAY_BASE_URL}/api/apps/{app_id}/permissions"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def get_datasafety(app_id):
    url = f"{GPLAY_BASE_URL}/api/apps/{app_id}/datasafety"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def flatten_criterias(review):
    flattened_criterias = {}
    for criteria in review.get("criterias", []):
        flattened_criterias[criteria["criteria"]] = criteria.get("rating")
    return flattened_criterias

def extract_all_reviews(app_id, upto_date=None):
    all_reviews = []
    next_pagination_token = None

    while True:
        data = get_reviews(app_id, next_pagination_token)
        if not data:
            break

        reviews = data.get("results", {}).get("data", [])
        next_pagination_token = data.get("results", {}).get("nextPaginationToken")

        if upto_date:
            reviews = [r for r in reviews if datetime.strptime(r["date"], "%Y-%m-%d").date() > upto_date]
            if len(reviews) == 0:
                break

        all_reviews.extend(reviews)

        if not next_pagination_token:
            break

    flattened_reviews = []
    for review in all_reviews:
        flattened_review = {
            "id": review["id"],
            "date": review["date"],
            "score": review["score"],
            "scoreText": review["scoreText"],
            "title": review["title"],
            "text": review["text"],
            **flatten_criterias(review),
        }
        flattened_reviews.append(flattened_review)

    return [dict(t) for t in {tuple(d.items()) for d in flattened_reviews}]

def save_app_reviews(app_id: str) -> None:
    """
    Save the reviews of a specific app into a JSON file.

    Args:
        app_id (str): The ID of the app for which the reviews need to be saved.

    Returns:
        None: The function does not return any value. It only saves the reviews into a file.
    """
    review_filename = '../raw-data/reviews/' + f"Reviews_{app_id}.json"
    existing_reviews = []

    if os.path.exists(review_filename):
        with open(review_filename) as review_file:
            existing_reviews = json.load(review_file)
    else:
        existing_reviews = []

    upto_date = (datetime.today() - timedelta(days=2)).date()
    reviews = extract_all_reviews(app_id, upto_date) if len(existing_reviews) > 0 else extract_all_reviews(app_id)
    logging.debug('Count of all reviews ' + len(reviews))
    all_reviews = remove_duplicates(existing_reviews + reviews)
    all_reviews = sorted(all_reviews, key=lambda x: (datetime.strptime(x["date"], "%Y-%m-%d"), x["id"]), reverse=True)
    with open(review_filename, 'w') as file:
        json.dump(all_reviews, file, indent=4)

def remove_duplicates(reviews: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate reviews from the list.

    Args:
        reviews (List[Dict[str, str]]): The list of reviews.

    Returns:
        List[Dict[str, str]]: The list of reviews without duplicates.
    """
    return [dict(t) for t in {tuple(d.items()) for d in reviews}]

def save_app_permissions(app_id: str) -> None:
    """
    This function saves app permissions to a JSON file.

    Args:
        app_id (str): The ID of the app for which the permissions need to be saved.

    Returns:
        None: The function saves the app permissions to a JSON file.
    """
    logging.log(logging.DEBUG, 'start of save_app_review_criterias')
    permission_filename = '../raw-data/reviews/' + f"Permissions_{app_id}.json"
    data = get_permissions(app_id)
    with open(permission_filename, 'w') as file:
        json.dump(data, file, indent=4)


def save_app_info(app_id: str) -> None:
    """
    This function saves app info to a JSON file.

    Args:
        app_id (str): The ID of the app for which the appinfo need to be saved.

    Returns:
        None: The function saves the app info to a JSON file.
    """
    logging.log(logging.DEBUG, 'start of save_app_review_criterias')
    permission_filename = '../raw-data/reviews/' + f"AppInfo_{app_id}.json"
    data = get_appinfo(app_id)
    with open(permission_filename, 'w') as file:
        json.dump(data, file, indent=4)

def save_app_datasafety(app_id: str) -> None:
    """
    This function saves app datasafety to a JSON file.

    Args:
        app_id (str): The ID of the app for which the datasafety need to be saved.

    Returns:
        None: The function saves the app datasafety to a JSON file.
    """
    logging.log(logging.DEBUG, 'start of save_app_review_criterias')
    datasafety_filename = '../raw-data/reviews/' + f"DataSafety_{app_id}.json"
    data = get_datasafety(app_id)
    with open(datasafety_filename, 'w') as file:
        json.dump(data, file, indent=4)

def save_app_review_criterias(app_id: str) -> None:
    """
    This function saves the counts of specific criteria in app reviews to a JSON file.

    Args:
        app_id (str): The ID of the app for which the review criteria counts need to be saved.

    Returns:
        None: The function saves the criteria counts to a JSON file.
    """
    logging.log(logging.DEBUG, 'start of save_app_review_criterias')
    review_filename = '../raw-data/reviews/' + f"Reviews_{app_id}.json"
    criterias_filename = '../raw-data/reviews/' + f"Criterias_{app_id}.json"

    if os.path.exists(review_filename):
        with open(review_filename, 'r') as review_file:
            existing_reviews = json.load(review_file)
    else:
        existing_reviews = []

    criteria_counts: Dict[str, int] = {}

    for single_review in existing_reviews:
        for key in single_review:
            if key.startswith("vaf"):
                criteria_counts[key] = criteria_counts.get(key, 0) + 1
    with open(criterias_filename, 'w') as file:
        json.dump(criteria_counts, file, indent=4)


if __name__ == "__main__":

    with open('../raw-data/applist.json') as f:
        app_ids = json.load(f)

    logging.basicConfig(filename='ExtractReviews' + time.strftime("%Y%m%d-%H%M%S") + '.log', 
                        format='%(asctime)s %(message)s', level=logging.DEBUG)
    
    for app_id in app_ids:
        save_app_info(app_id)
        save_app_reviews(app_id)
        save_app_review_criterias(app_id)
        save_app_permissions(app_id)
        save_app_datasafety(app_id)
        