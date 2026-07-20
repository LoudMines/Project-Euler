import Constants, Scraper
import os
import re
import nbformat as nbf

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

# Function to create a problem file with its description and title from a template.
# If a number is given, that problem is created if it does not exist yet. Else, the problem with the lowest number
# For which there is no file yet is created.
def create_problem(number= None):
    if number in get_existing_problem_files():
        raise Exception(f"File for problem {number} already exists")
    next_problem = number if number else get_next_problem()
    next_problem_filename = Constants.PROBLEM_FOLDER + "/P" + str(next_problem).zfill(3) + ".ipynb"

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