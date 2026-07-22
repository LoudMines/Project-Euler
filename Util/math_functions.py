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
def inner_eratosthenes(n, prime_mask):
    prime = 2
    while prime ** 2 <= n:
        if prime_mask[prime]:
            j = prime ** 2
            while j <= n:
                prime_mask[j] = False
                j += prime
        prime += 1
    return [mask_index for mask_index, prime in enumerate(prime_mask) if prime]

@jit(nopython=True)
def sieve_eratosthenes(n):
    # An array which holds whether a number is prime, 0 and 1 are False, after that we can index
    # by the prime number
    prime_mask = [False, False] + ([True] * (n - 1))
    return inner_eratosthenes(n, prime_mask)


@jit(nopython=True)
def sieve_eratosthenes_odd(n):
    # I saw the odd only mentioned somewhere without explanation. This is my implementation of that idea
    prime_mask = [False, False, True] + ([True, False] * ((n - 2) // 2))
    if n % 2 != 0:
        prime_mask.append(True)
    return inner_eratosthenes(n, prime_mask)


# Weird more complex sieve, I don't fully understand it and it is incorrect atm.
@jit(nopython=True)
def sieve_sundaram(n):
    k = (n - 3) // 2 + 1
    integer_list = ([True] * (k + 1))
    for i in range((math.ceil(math.sqrt(n)) - 3) // 2 + 1):
        p = 2 * i + 3
        s = (p * p - 1) // 2
        for j in range(s, k + 1, p):
            integer_list[j] = False
    return [2] + [2 * i + 1 for i, value in enumerate(integer_list) if value and i != 0]

trial_sum = sum(m for m in range(2, 2000000) if is_prime(m))
sundaram_sum = sum(sieve_sundaram(2000000))
print("trial:", trial_sum)
print("sundaram:", sundaram_sum)
print("match:", trial_sum == sundaram_sum)