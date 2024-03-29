from django.core.validators import (
    MinValueValidator, RegexValidator, MaxValueValidator
)
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint

from recipes import constants
from users.models import User


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        "Название ингредиента",
        max_length=constants.RECIPE_NAME_AND_TAGS,
        null=False
    )
    measurement_unit = models.CharField(
        "Единица для измерения", max_length=constants.RECIPE_NAME_AND_TAGS
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)
        constraints = [
            UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingregient_name_measurement_unit"
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тэга."""

    name = models.CharField(
        "Название тэга", unique=True,
        max_length=constants.RECIPE_NAME_AND_TAGS
    )
    color = models.CharField(
        "Цветовой HEX-код",
        null=True,
        max_length=constants.TAG_COLOR,
        validators=[RegexValidator(
            r"^#([a-fA-F0-9]{6})", message="Введите HEX!"
        )]

    )
    slug = models.SlugField(
        "Слаг", unique=True, max_length=constants.RECIPE_NAME_AND_TAGS
    )

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        related_name="recipes",
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Автор",
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления",
        validators=[MinValueValidator(
            constants.INGREDIENT_MIN_AMOUNT,
            message="Время готовки должно быть не меньше чем 1 минута"
        ), MaxValueValidator(
            constants.INGREDIENT_MAX_AMOUNT,
            message=f"Время готовки должно"
                    f" быть меньше "
                    f"чем {constants.INGREDIENT_MAX_AMOUNT} минут"
        )]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name="recipes",
        verbose_name="Ингредиенты",
        through="RecipeIngredients"
    )
    text = models.TextField(
        "О рецепте",
    )
    image = models.ImageField(
        "Изображение рецепта", upload_to="recipes/"
    )
    name = models.CharField(
        "Название рецепта", max_length=constants.RECIPE_NAME_AND_TAGS
    )
    tags = models.ManyToManyField(
        Tag, related_name="recipes", verbose_name="Тэги"
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации рецепта",
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """Модель ингредиентов в рецептах"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество ингредиента",
        validators=[
            MinValueValidator(constants.INGREDIENT_MIN_AMOUNT),
            MaxValueValidator(constants.INGREDIENT_MAX_AMOUNT)
        ],
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"

    def __str__(self):
        return (
            f"В рецепте {self.recipe},"
            f" {self.ingredient} содержится" f"{self.amount}."
        )


class UserRecipe(models.Model):
    """Абстрактный класс для покупок и избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        unique_together = ("user", "recipe")

    def clean(self):
        if self.__class__.objects.filter(
                user=self.user, recipe=self.recipe
        ).exists():
            raise ValidationError(
                "Пользователь уже добавил этот рецепт."
            )
        if self.__class__.objects.filter(
                user=self.user, name=self.name
        ).exists():
            raise ValidationError(
                "Пользователь уже имеет список с таким именем."
            )
        return super().save(self)

    def __str__(self):
        return "{} В {} у {}".format(self.recipe, self.__str__(), self.user)


class Favourite(UserRecipe):
    """Наследник абстрактного класса для избранного."""
    class Meta(UserRecipe.Meta):
        default_related_name = "favourites_recipe"
        verbose_name = "Избранные рецепты"
        verbose_name_plural = "Избранные рецепты"


class ShoppingCartList(UserRecipe):
    """Наследник абстрактного класса для покупок."""
    class Meta(UserRecipe.Meta):
        default_related_name = "shopping_recipe"
        verbose_name = "Список для покупок"
        verbose_name_plural = "Списки для покупок"
