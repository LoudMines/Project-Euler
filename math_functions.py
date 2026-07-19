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

"""
-------------------- Prime Sieves --------------------
Used to generate all primes up to n. The most basic is Eratosthenes, 
faster sieves will be implemented later.
"""

@jit(nopython=True)
def sieve_eratosthenes(n):
    # An array which holds whether a number is prime, 0 and 1 are False, after that we can index
    # by the prime number
    prime_mask = [False, False] + ([True] * (n - 1))
    for prime in range(2, math.ceil(math.sqrt(n))):
        if prime_mask[prime]:
            j = prime ** 2
            while j <= n:
                prime_mask[j] = False
                j += prime
    return [mask_index for mask_index, prime in enumerate(prime_mask) if prime]