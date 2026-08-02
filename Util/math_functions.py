import math
from numba import njit
import numpy as np

@njit
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

# This can be used by any function which needs a sieve without thinking about it.
# It uses whichever sieve has been determined to be fastest (currently determined in P010)
@njit
def prime_sieve(n):
    return sieve_eratosthenes_wheel(n)

# The most basic sieve. Was made much faster by using np arrays instead of lists. The dtype is crucial for this.
@njit
def sieve_eratosthenes(n):
    # An array which holds whether a number is prime, 0 and 1 are False, after that we can index
    # by the prime number
    prime_mask = np.ones(n + 1, dtype=np.bool_)
    prime_mask[:2] = False
    prime = 2
    while prime ** 2 <= n:
        if prime_mask[prime]:
            prime_mask[prime ** 2 : n + 1 : prime] = False
        prime += 1
    return np.where(prime_mask)[0]

@njit
def sieve_eratosthenes_odd(n):
    # I saw the odd only mentioned somewhere without explanation. This is my implementation of that idea
    prime_mask = np.ones(n + 1, dtype=np.bool_)
    prime_mask[:2] = False
    prime_mask[4::2] = False

    # All even numbers are already set to false, we can start with 3 and increment by 2 to only check odd
    prime = 3
    while prime ** 2 <= n:
        if prime_mask[prime]:
            prime_mask[prime ** 2 : n + 1 : prime] = False
        prime += 2
    return np.where(prime_mask)[0]

@njit
def sieve_eratosthenes_wheel(n, wheel_n= 4):
    """
    The wheel will be a 2d array, with only the rows where primes can be remaining. In the case of wheel one, the
    factors are: [2,3] so the wheel size is 2 * 3 = 6. This means any number can be written in the form

    6k + 1, 6k +2, 6k + 3, 6k + 4, 6k + 5 or 6k

    Out of these options, all primes are in 6k + 1 and 6k + 5, as these are coprime with our initial factors.

    In general, for a given set of prime factors to start with, the size of the wheel is the product of those factors.

    The number of "blocks" of our number definitions we need to loop over are equal to n // wheel_size

    The sections which contain the primes can be determined by finding the numbers between 1 and wheel size which are
    not divisible by any of the original factors.

    In our example, these are the remainders [1,5].

    Out of our original way of writing all numbers, we now only need to check the numbers in the form
    6k + 1 and 6k + 5. Leaving us with a wheel of shape (num_blocks, len(remainders)).

    We then loop through the possible remainders. Within this loop, we loop through k in the range 1 - num_blocks
    to check the possible prime numbers of the form wheel_size * k + remainder
    """
    if wheel_n > 5:
        raise Exception(f"Wheel size {wheel_n} is inadvisably large.")
    first_primes = np.array([2, 3, 5, 7, 11, 13])
    wheel_primes = first_primes[:wheel_n]
    wheel_size = np.prod(wheel_primes)

    # The number of blocks needed to fit the wheel to n
    num_blocks = math.ceil(n / wheel_size)

    remainder_mask = np.ones(wheel_size, dtype=np.bool_)
    for r in range(wheel_size):
        for factor in wheel_primes:
            if r % factor == 0:
                remainder_mask[r] = False
                break

    remainders = np.where(remainder_mask)[0]
    num_remainders = len(remainders)

    remainder_to_index = np.full(wheel_size, -1, dtype=np.int64)
    for i in range(num_remainders):
        remainder_to_index[remainders[i]] = i

    # For each combination of a possible prime with a composite of the form a * prime, there exists a smallest delta,
    # for which: if we add delta * prime to the composite, the remainder of the new composite is again in the
    # remainders we need to investigate. What follows are lookup tables to get the next delta and the next remainder
    # index given the composite remainder and the prime remainder

    next_delta = np.zeros((num_remainders, num_remainders), dtype=np.int64)
    next_remainder_index = np.zeros((num_remainders, num_remainders), dtype=np.int64)

    for remainder_index in range(num_remainders):
        for prime_remainder_index in range(num_remainders):
            composite = remainders[remainder_index]
            prime = remainders[prime_remainder_index]
            x = 1
            while True:
                next_composite_remainder = (composite + x * prime) % wheel_size
                if remainder_to_index[next_composite_remainder] != -1:
                    next_delta[remainder_index, prime_remainder_index] = x
                    next_remainder_index[remainder_index, prime_remainder_index] = remainder_to_index[next_composite_remainder]
                    break
                x += 1

    wheel = np.ones((num_remainders, num_blocks), dtype=np.bool_)
    wheel[0,0] = False

    for remainder_index in range(num_remainders):
        for k in range(num_blocks):
            if wheel[remainder_index, k]:
                prime_remainder = remainders[remainder_index]
                possible_prime = wheel_size * k + prime_remainder
                if possible_prime >= first_primes[wheel_n]:
                    composite = possible_prime ** 2
                    composite_remainder_index = remainder_to_index[composite % wheel_size]
                    while composite <= n:
                        composite_index = composite // wheel_size
                        wheel[composite_remainder_index, composite_index] = False
                        delta = next_delta[composite_remainder_index, remainder_index]
                        composite += delta * possible_prime
                        composite_remainder_index = next_remainder_index[composite_remainder_index, remainder_index]

    found_primes = wheel.sum()
    primes = np.empty(found_primes + wheel_n, dtype=np.int64)
    count = wheel_n
    primes[:count] = wheel_primes
    for index in range(num_blocks):
        for r in range(num_remainders):
            if wheel[r, index]:
                # print(wheel_size, index, remainders[r])
                prime = wheel_size * index + remainders[r]
                if prime <= n:
                    primes[count] = prime
                    count += 1

    return primes[:count]

@njit
def sieve_eratosthenes_segmented(n):
    delta = math.ceil(math.sqrt(n))
    # We only need to sieve up to sqrt(n), so using this list for all sieving will suffice
    base_primes = sieve_eratosthenes_odd(delta - 1)

    # Upper bound for pi(n)
    max_primes = int(1.2 * n / math.log(n))
    all_primes = np.empty(max_primes, dtype=np.int64)

    count = len(base_primes)
    all_primes[:count] = base_primes

    segment_primes = np.ones(delta, dtype=np.bool_)

    for segment in range(1, delta):
        segment_start = segment * delta
        if segment_start > n:
            break
        # The last segment might continue past n, if this is the case, the segment end is set to n
        segment_end = min((segment + 1) * delta, n + 1)

        segment_size = segment_end - segment_start
        segment_primes[:segment_size] = True
        for prime in base_primes:
            if prime ** 2 > segment_end:
                break
            start_index = math.ceil(segment_start / prime) * prime - segment_start
            segment_primes[start_index:segment_size:prime] = False

        for i in range(segment_size):
            if segment_primes[i]:
                all_primes[count] = segment_start + i
                count += 1
    return all_primes[:count]

@njit
def sieve_eratosthenes_two_segments(n):
    delta = math.ceil(math.sqrt(n))
    # We only need to sieve up to sqrt(n), so using this list for all sieving will suffice
    base_primes = sieve_eratosthenes_odd(delta)

    # Upper bound for pi(n)
    max_primes = int(1.2 * n / math.log(n))
    all_primes = np.empty(max_primes, dtype=np.int64)

    count = len(base_primes)
    all_primes[:count] = base_primes
    segment_size = n - delta

    prime_mask = np.ones(segment_size, dtype=np.bool_)

    for prime in base_primes:
        start_index = math.ceil(delta / prime) * prime - delta
        prime_mask[start_index:segment_size:prime] = False
    for i in range(segment_size):
        if prime_mask[i]:
            all_primes[count] = i + delta
            count += 1
    return all_primes[:count]

# Weird more complex sieve, I don't fully understand it and it is incorrect atm.
@njit
def sieve_sundaram(n):
    k = (n - 3) // 2 + 1
    prime_mask = np.ones(k + 1, dtype=np.bool_)
    prime_mask[0] = False
    for i in range((math.ceil(math.sqrt(n)) - 3) // 2 + 1):
        p = 2 * i + 3
        s = (p * p - 1) // 2
        prime_mask[s:k + 1: p] = False
    return np.concatenate((np.array([2]), (2 * np.where(prime_mask)[0] + 1)))

"""
-------------------- Prime factorisation --------------------
Functions for factorisation. The prime factorisation was extracted from P003 as it worked best there, but I have not
investigated if it is optimal (it's probably not) this warrants further investigation but for now it will suffice.

"""

@njit
def get_prime_factors(n):
    i = 2
    remainder = n
    prime_factors = []
    while True:
        if remainder % i == 0:
            remainder /= i
            prime_factors.append(i)
        elif i == 2:
            i += 1
        else:
            i += 2
        if remainder == 1:
            break
    return prime_factors

"""
-------------------- Triangular numbers --------------------

"""

@njit
def get_triangular_number(n):
    return n * (n + 1) // 2

@njit
def get_triangular_root(number):
    return (math.sqrt(8 * number + 1) - 1) / 2