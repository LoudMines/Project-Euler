from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PROBLEM_FOLDER = PROJECT_ROOT.joinpath("Problems")
PROBLEM_TEMPLATE = PROBLEM_FOLDER.joinpath("P.ipynb")
PROBLEM_NB_VERSION = 4