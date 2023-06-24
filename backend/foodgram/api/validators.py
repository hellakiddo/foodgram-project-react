import re

from django.core.exceptions import ValidationError

from users.models import Subscribe


def validate(self, value):
    author = self.instance
    user = self.context.get('request').user
    if Subscribe.objects.filter(author=author, user=user).exists():
        raise ValidationError(
            'Вы уже подписаны на этого автора.',
        )
    if user == author:
        raise ValidationError(
            'Подписаться на самого себя невозможно.',
        )
    return value


def validate_regex_username(value):
    """Проверка на отсутсвие запрещенных символов."""
    forbidden_symbols = ''.join(set(re.sub(r'^[\w.@+-]+$', '', value)))
    if forbidden_symbols:
        raise ValidationError(
            f'Некорректный символ для никнейма: {forbidden_symbols}'
            f' Только буквы, цифры и @/./+/-/_'
        )
    return value