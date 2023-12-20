from functools import lru_cache

# ANSI color codes
RED = 31
GREEN = 32
YELLOW = 33
BLUE = 34
PURPLE = 35
CYAN = 36

CLEAR = '\033[0m'
COLORS = [f'\033[{c}m' for c in [YELLOW, GREEN, CYAN, BLUE, PURPLE, RED]]


from subprocess import check_output as sh

@lru_cache(maxsize=-1)
def term_width():
    return int(sh(("tput", "cols")))

def print_rjust(text, width=None):
    width = width or term_width()
    print(text.rjust(width), flush=True)
