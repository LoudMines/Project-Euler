import contextlib
import io

from Util import Constants, Scraper
import os
import re
import nbformat as nbf

from datetime import datetime
from Util.Problems import Problem
import Util.Problems as ProblemsModule
import pandas as pd
import multiprocessing as mp

# Returns a list of integers of the problem numbers for which there are files
def get_existing_problem_files():
    file_list = os.listdir(Constants.PROBLEM_FOLDER)
    pattern = re.compile(r"P[0-9]+\.ipynb")
    problems = []
    for file in file_list:
        if pattern.match(file):
            problems.append(int(file[1:4]))
    return problems

# Returns the lowest integer for which there is no file yet
def get_next_problem():
    existing_files = get_existing_problem_files()
    problem = 0
    while True:
        if problem not in existing_files:
            return problem
        problem += 1

def create_problem(number= None):
    """
    Function to create a problem file with its description and title from a template.

    If a number is given, that problem is created if it does not exist yet. Else, the problem with the
    lowest number for which there is no file yet is created.
    """

    if number in get_existing_problem_files():
        raise Exception(f"File for problem {number} already exists")
    next_problem = number if number else get_next_problem()
    next_problem_filename = Constants.PROBLEM_FOLDER.joinpath("P" + str(next_problem).zfill(3) + ".ipynb")

    nb = nbf.read(Constants.PROBLEM_TEMPLATE, as_version= Constants.PROBLEM_NB_VERSION)

    title, desc = Scraper.get_problem_info(next_problem)

    replacements = {
        "999": str(next_problem).zfill(3),
        "888": str(next_problem),
        "{TITLE}": title,
        "{DESCRIPTION}": desc,
    }

    for cell in nb.cells:
        for placeholder, value in replacements.items():
            cell.source = cell.source.replace(placeholder, value)

    nbf.write(nb, next_problem_filename)

    return f"✔️ Created the file for problem {next_problem}! (If you do not see it, press ctrl+alt+y) "

"""
The following functions are for the table of results, loading the results, saving them to csv etc.
"""

RESULT_COLUMNS = ["number", "title", "description", "time_ms", "solver", "is_best", "is_first", "tested_at"]

def load_results(path=Constants.RESULTS_TABLE_PATH):
    if not os.path.exists(path):
        return pd.DataFrame(columns=RESULT_COLUMNS)
    df = pd.read_csv(path)
    for col in RESULT_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[RESULT_COLUMNS]


def save_results(df, path=Constants.RESULTS_TABLE_PATH):
    df = df.sort_values("number").reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def notebook_path(number):
    return Constants.PROBLEM_FOLDER.joinpath("P" + str(number).zfill(3) + ".ipynb")


def run_problem(number, repeats=1000):
    path = notebook_path(number)
    if not path.exists():
        raise Exception(f"No notebook file found for problem {number}")

    nb = nbf.read(path, as_version=Constants.PROBLEM_NB_VERSION)

    namespace = {}
    original_display = ProblemsModule.display
    ProblemsModule.display = None  # the describe() function of problems uses print(). Below we supress all
    # print() and display() calls.
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            for cell in nb.cells:
                if cell.get("cell_type") == "code":
                    code = cell.get("source", "")
                    # Do not run the cells which are meant for testing the code, we will test the code on
                    # our own terms.
                    if not (("test_all(" in code) or ("test_once(" in code)):
                        exec(code, namespace)
    finally:
        ProblemsModule.display = original_display

    # A problem instance should be created after running the code. The following code can be used to create one
    # if none exists, but this should not be necessary.
    problem_instance = next((v for v in namespace.values() if isinstance(v, Problem)), None)
    if problem_instance is None:
        raise Exception(f"Could not find a Problem instance in P{str(number).zfill(3)}.ipynb")

    results = problem_instance.get_results(repeats=repeats)
    if not results:
        raise Exception(f"Problem {number} has no solutions implemented yet")

    # We use the solution which is marked as best. If none is marked as best, use the fastest one.
    solution = (next((r for r in results if r["is_best"]), None)
              or min(results, key=lambda r: r["time_ms"]))

    return {
        "number": problem_instance.number,
        "title": problem_instance.title,
        "description": problem_instance.description,
        "time_ms": solution["time_ms"],
        "solver": solution["name"],
        "is_first": bool(solution["is_first"]),
        "is_best": bool(solution["is_best"])
    }


"""
Some multi-processing black magic. When you call run_problem from the dashboard, it is run on a thread. I'm not 
entirely sure why that is, but when numba compilation is run on a non-main thread, it tends to break, so this process 
is needed to prevent crashes. 
"""

def run_problem_worker(queue, number, repeats):
    try:
        queue.put(("ok", run_problem(number, repeats)))
    except Exception as e:
        queue.put(("error", str(e)))


def run_problem_isolated(number, repeats=1000, timeout=120):
    context = mp.get_context("spawn")
    result_queue = context.Queue()
    process = context.Process(target=run_problem_worker, args=(result_queue, number, repeats))
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        raise Exception(
            f"Problem {number} timed out after {timeout}s and was killed "
            f"- check for an infinite loop or an unexpectedly slow solution."
        )

    status, payload = result_queue.get()
    if status == "error":
        raise Exception(f"Problem {number} failed while running: {payload}")
    return payload


def update_row(df, row):
    row = {**row, "tested_at": datetime.now().isoformat()}
    df = df[df["number"] != row["number"]]
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    return df


def rows_for_numbers(df, numbers):
    if not numbers:
        return []
    subset = df[df["number"].isin(numbers)].sort_values("number")
    return subset.to_dict(orient="records")


def get_problem_results(progress_bar=None, repeats=1000):
    """
    Returns the results of each problem if the results have already been saved. If not, it runs the problem
    to get the results and updates the table.

    progress_bar: pass a tqdm() object, and it will be updated as the code runs.
    """
    df = load_results()
    existing_numbers = set(get_existing_problem_files())
    db_numbers = set(df["number"].tolist())
    missing = sorted(existing_numbers - db_numbers)

    if len(missing) > 0:
        if progress_bar is not None:
            progress_bar.total = len(missing)

        for i, number in enumerate(missing, start=1):
            row = run_problem_isolated(number, repeats=repeats)
            df = update_row(df, row)
            if progress_bar:
                progress_bar.update(1)

    if missing:
        df = save_results(df)

    return rows_for_numbers(df, existing_numbers)


def rerun_problem(number, repeats=1000):
    """
    Re-run a single problem. Useful if the solution got improved to update the table.
    """
    df = load_results()
    row = run_problem_isolated(number, repeats=repeats)
    df = update_row(df, row)
    save_results(df)
    return row


def reset_database(repeats=1000, progress_bar=None):
    """
    Deletes all stored results and re-runs each problem.

    !!! This should only be called after warning the user, as this will take a long time and delete
    all existing records of tests. !!!
    """
    save_results(pd.DataFrame(columns=RESULT_COLUMNS))
    return get_problem_results(repeats=repeats, progress_bar=progress_bar)
