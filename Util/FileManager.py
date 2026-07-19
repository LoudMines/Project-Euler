import Constants
import os
import re
import shutil

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

def create_problem():
    # next_problem = get_next_problem()
    # next_problem_filename = Constants.PROBLEM_FOLDER + "/P" + str(next_problem).zfill(3) + ".ipynb"
    # shutil.copyfile(Constants.PROBLEM_TEMPLATE, next_problem_filename)
    with open(Constants.PROBLEM_TEMPLATE, "a") as f:
        print(f.read())

create_problem()
