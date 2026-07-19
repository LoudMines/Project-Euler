import math
from numba import jit

@jit(nopython=True)
def is_prime(n):
    if n < 2:
        return False

    if n <= 3:
        return True

    if n % 2 == 0 or n % 3 == 0:
        return False

    limit = int(math.sqrt(n))
    i = 1
    while (6 * i - 1) <= limit:
        if (n % (6 * i - 1) == 0) or (n % (6 * i + 1) == 0):
            return False
        else:
            i += 1
    return True