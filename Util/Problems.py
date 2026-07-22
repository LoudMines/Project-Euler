import time
from numba import jit as jit

try:
    from IPython.display import display, Markdown
except ImportError:
    display = Markdown = None

# Decorator for any solution function, this will add it to the functions which get tested
# Setting make_fast to True uses numba jit on the function
def solution(cls, message= None,
             first= False,
             best= False,
             make_fast= False,
             jit_kwargs= None,
             warmup_args=()):
    jit_kwargs = jit_kwargs or {"nopython": True, "cache": True}
    def decorator(func):
        name = func.__name__
        target = jit(**jit_kwargs)(func) if make_fast else func

        # Run jitted functions once to compile them.
        target(*warmup_args)

        def method(_):
            result = target(*warmup_args)
            return result
        method._is_solution = True
        method._is_first = first
        method._is_best = best
        setattr(cls, name, method)
        return target
    return decorator

class Problem:
    number: int = None
    title: str = ""
    description: str = ""

    def describe(self):
        text = f"## Problem {self.number}: {self.title}\n\n{self.description}"
        if display and Markdown:
            display(Markdown(text))
        else:
            print(text)

    # Returns all the names of functions which have the solution decorator
    def _solution_names(self):
        return [
            name for name in dir(type(self))
            if not name.startswith("_")
               and getattr(getattr(type(self), name), "_is_solution", False)
        ]

    def test_all(self, repeats=1000):
        names = self._solution_names()
        if not names:
            print("No solutions implemented yet.")
            return
        for name in names:
            method = getattr(self, name)
            start_time = time.perf_counter()
            for _ in range(repeats):
                result = method()
            time_taken = (time.perf_counter() - start_time) / repeats * 1000
            tag = (" (best)" if getattr(method, "_is_best", False) else
                   " (first)" if getattr(method, "_is_first", False) else
                   "")
            print(f"{result} found in {time_taken:.6f} ms by {name}{tag}")