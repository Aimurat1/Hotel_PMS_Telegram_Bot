import random
import string

def random_symbols():
    symbols = string.ascii_letters + string.digits # a string of all possible symbols
    random_symbols = ''.join(random.choice(symbols) for i in range(10)) # a random string of 8 symbols
    return random_symbols