import time
import requests


def make_request_with_retry(url: str, headers: dict, payload: dict, retries: int = 3) -> dict:
    """
    Makes an HTTP request with retry logic and exponential backoff.

    :param url: str, The API URL
    :param headers: dict, Request headers
    :param payload: dict, Request payload
    :param retries: int, Maximum number of retries
    :return: dict, The API response
    """
    for attempt in range(retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                wait_time = 2 ** attempt
                
                print(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Max retries exceeded. Error: {e}")