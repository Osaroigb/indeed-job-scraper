from concurrent.futures import ThreadPoolExecutor, as_completed


def limit_concurrency(tasks: list, handler, max_concurrent: int = 5) -> list:
    """
    Limits the number of concurrent tasks.

    :param tasks: list, Tasks to process
    :param handler: function, Handler function for processing each task
    :param max_concurrent: int, Maximum concurrent tasks
    :return: list, Results of processed tasks
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_to_task = {executor.submit(handler, task): task for task in tasks}

        for future in as_completed(future_to_task):
            try:
                results.append(future.result())

            except Exception as e:
                print(f"Task failed: {e}")

    return results