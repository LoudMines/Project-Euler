import numpy as np
from numba.experimental import jitclass
from numba import njit
import numba as nb

"""
Because this has to be a jitclass (it needs to be created inside jit functions) All of this is very
janky. I cannot do any type checks, so all functions of the class fully rely on the user making no mistakes.

!IMPORTANT!
See the function at the bottom, because of numba jank, you can't just create a bigint yourself.
"""

@njit
def remove_lead_zeros(np_array):
    lead_zeros = 0
    for i in range(len(np_array) - 1, -1, -1):
        if np_array[i] == 0:
            lead_zeros += 1
        else:
            break
    return np_array[:len(np_array) - lead_zeros]

spec = [
    ('value_string', nb.types.string),
    ('initial_size', nb.int_),
    ('multiplier', nb.int_),
    ('initial_array', nb.int8[:]),
    ('value', nb.int8[:])
]

@jitclass(spec)
class BigInt:
    def __init__(self, value_string,
                 initial_size= 0,
                 initial_array=np.zeros((0,), dtype=np.int8)):
        self.value_string = value_string
        initial_size = max(initial_size, len(value_string), len(initial_array))
        if len(initial_array) == 0:
            self.value = np.zeros((initial_size,), dtype=np.int8)
            digit_index = 0
            for i in range(len(value_string) - 1, -1, -1):
                self.value[digit_index] = ord(value_string[i]) - 48 # String to int
                digit_index += 1
        else:
            self.value = np.zeros((initial_size,), dtype=np.int8)
            for i, digit in enumerate(initial_array):
                self.value[i] = digit
        self.value = remove_lead_zeros(self.value)

    def digits(self):
        return len(self.value)

    def __add__(self, other_bigint):
        own_digits = self.digits()
        other_digits = other_bigint.digits()
        most_digits = max(own_digits, other_digits)
        sum_array = np.zeros((most_digits + 1,), dtype=np.int8)
        carry = 0
        for digit in range(most_digits + 1):
            own_digit = self.value[digit] if digit < own_digits else 0
            other_digit = other_bigint.value[digit] if digit < other_digits else 0
            digit_sum = own_digit + other_digit + carry
            if digit_sum > 9:
                carry = 1
                sum_array[digit] = digit_sum % 10
            else:
                carry = 0
                sum_array[digit] = digit_sum
        return BigInt("", 0, sum_array)

    def __mul__(self, multiplier):
        new_bigint = self
        for i in range(multiplier - 1):
            new_bigint += self
        return new_bigint

    def __str__(self):
        lead_zeros = True
        result_string = ""
        for i in range(len(self.value) - 1, -1, -1):
            if lead_zeros:
                if self.value[i] == 0:
                    continue
            lead_zeros = False
            result_string += str(self.value[i])
        return result_string

# There is a bug in numba which causes an error if you try to use the default args of a jitclass. This bigint
# builder should therefore be used in any njit functions.
@njit
def make_bigint(value_string,
                initial_size=0,
                initial_array=np.zeros((0,), dtype=np.int8)):
    return BigInt(value_string, initial_size, initial_array)