    

import random


def make_rng(seed: int) -> random.Random:
    """Create a random number generator with a fixed seed."""
    import random
    rng = random.Random(seed)
    return rng

