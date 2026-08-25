import time

from PIL.ImageChops import constant
from numba import njit as njit
from numba import jit as jit

try:
    from IPython.display import display, Markdown
except ImportError:
    display = Markdown = None

# Decorator for any solution function, this will add it to the functions which get tested
# Setting make_fast to True uses numba jit on the function
def solution(cls,
             first= False,
             best= False,
             make_fast= False,
             max_tests = None,
             jit_kwargs= None,
             warmup_args=()):
    jit_kwargs = jit_kwargs or {}
    def decorator(func):
        name = func.__name__
        if jit_kwargs:
            target = jit(**jit_kwargs)(func) if make_fast else func
        else:
            target = njit()(func) if make_fast else func

        # Run jitted functions once to compile them.
        if make_fast:
            target(*warmup_args)

        def method(_):
            result = target(*warmup_args)
            return result
        method._is_solution = True
        method._is_first = first
        method._is_best = best
        if max_tests is not None: method._max_tests = max_tests
        setattr(cls, name, method)
        return target
    return decorator

class Problem:
    number: int = None
    title: str = ""
    description: str = ""
    separate_test_results = {}

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

    def get_results(self, repeats=1000):
        names = self._solution_names()
        results = []
        for name in names:
            method = getattr(self, name)
            method_repeats = getattr(method, "_max_tests", repeats)
            if method_repeats == 0:
                continue
            start_time = time.perf_counter()
            for _ in range(method_repeats):
                result = method()
            time_taken = (time.perf_counter() - start_time) / method_repeats * 1000
            results.append({
                "name": name,
                "result": result,
                "time_ms": time_taken,
                "repeats": method_repeats,
                "is_best": getattr(method, "_is_best", False),
                "is_first": getattr(method, "_is_first", False),
            })
        return results


    def test_all(self, repeats=1000):
        names = self._solution_names()
        if not names:
            print("No solutions implemented yet.")
            return

        printed = False
        for result in self.get_results(repeats):
            plural = "s" if result["repeats"] > 1 else ""
            tag = (" (best)" if result["is_best"] else
                   " (first)" if result["is_first"] else
                   "")
            print(f"{result['result']} found after "
                  f"{result['repeats']} test{plural} in "
                  f"{result['time_ms']:.6f} ms by "
                  f"{result['name']}{tag}")
            printed = True


        for name in names:
            method = getattr(self, name)
            if getattr(method, "_max_tests", repeats) == 0:
                if name in self.separate_test_results:
                    print(self.separate_test_results[name])
                    printed = True
        if not printed:
            print("No solutions implemented yet.")

    # If a solution is very slow, it's max_tests can be set to 0 so it won't get tested each time. This function can
    # then be used to run the function once and save the result, so it can be used in comparisons.
    def test_once(self, solution_to_test):
        method = getattr(self, solution_to_test)
        start_time = time.perf_counter()
        result = method()
        time_taken = (time.perf_counter() - start_time) * 1000
        tag = (" (best)" if getattr(method, "_is_best", False) else
               " (first)" if getattr(method, "_is_first", False) else
               "")
        result_string = f"{result} found after a separate test in {time_taken:.6f} ms by {solution_to_test}{tag}"
        self.separate_test_results[solution_to_test] = result_string
        print(result_string)
