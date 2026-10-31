from dataset import add_skill_flags, validate
from generate_data import generate


def raw_students(n=400, seed=7):
    return generate(n, seed)


def students(n=400, seed=7):
    return add_skill_flags(validate(generate(n, seed)))
