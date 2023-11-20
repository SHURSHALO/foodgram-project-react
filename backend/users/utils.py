from enum import Enum


class Role(Enum):
    user = 'пользователь'
    moderator = 'модератор'
    admin = 'администратор'

    @classmethod
    def get_role(cls):
        return [(role.name, role.value) for role in cls]
