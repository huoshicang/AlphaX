import random

def gen_random_same_length():
    length = 16
    lower = 10 ** (length - 1)   # 最小：1000000000000000
    upper = 10 ** length - 1     # 最大：9999999999999999
    return random.randint(lower, upper)
