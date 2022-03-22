import random
import string

from typing import Dict
from app.common.const import get_settings
from app.database.schema import Users


settings = get_settings()


def random_string() -> str:
    characters = string.ascii_letters
    word_lenght = random.randint(0, 10)
    random_word_list = random.sample(characters, word_lenght)
    return "".join(random_word_list)


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def check_superuser(user: Users) -> bool:
    return user.is_superuser


def check_status(user: Users) -> str:
    return user.status.name
