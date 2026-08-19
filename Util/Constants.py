from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PROBLEM_FOLDER = PROJECT_ROOT.joinpath("Problems")
PROBLEM_FILES_FOLDER = PROBLEM_FOLDER.joinpath("Problem_files")
PROBLEM_TEMPLATE = PROBLEM_FOLDER.joinpath("P.ipynb")
PROBLEM_NB_VERSION = 4

RESULTS_TABLE_PATH = PROJECT_ROOT.joinpath("Results.csv")