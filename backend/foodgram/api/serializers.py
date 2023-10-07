from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator
from rest_framework import status

from recipes.models import (Favourite, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCartList, Tag)
from users.models import Subscribe, User
class UserCreationSerializer(UserCreateSerializer):
    """Создание пользователей."""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
class UserCreateSerializer(UserSerializer):
    """Сериалайзер для создания и получение списка пользователей."""
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        if (self.context.get('request')
                and not self.context['request'].user.is_anonymous):
            return Subscribe.objects.filter(
                user=self.context['request'].user,
                author=obj
            ).exists()
        return False

class SubscribeShortRecipeSerializer(serializers.ModelSerializer):
    """Короткий сериалайзел рецепта."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериалайзер для вывода подписок пользователя."""
    is_subscribed = SerializerMethodField()
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()
    email = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        return obj.recipes.all()

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return Subscribe.objects.filter(
            user=request.user, author=obj
        ).exists()

class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписки."""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return Subscribe.objects.filter(
            author=obj.author, user=user).exists()

    def get_recipes(self, obj):
        limit = self.context.get('request').GET.get('recipes_limit')
        recipe_obj = obj.author.recipes.all()
        if limit:
            recipe_obj = recipe_obj[:int(limit)]
        serializer = SubscribeShortRecipeSerializer(recipe_obj, many=True)
        return serializer.data
class FavouriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для избранного."""
    class Meta:
        model = Favourite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favourite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в избранном.'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscribeShortRecipeSerializer(
            instance.recipe,
            context={'request': request},
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер тэга."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер ингредиента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты для рецепта."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    class Meta:
        model = RecipeIngredients
        fields = (
            'id', 'name', 'measurement_unit', 'amount'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериалайзер для списка рецептов."""
    author = UserCreateSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_in_shopping_cart(self, obj):
        return (self.context.get('request').user.is_authenticated
                and ShoppingCartList.objects.filter(
                    user=self.context['request'].user,
                    recipe=obj
                ).exists()
                )

    def get_is_favorited(self, obj):
        return (self.context.get('request').user.is_authenticated
                and Favourite.objects.filter(
                    user=self.context['request'].user,
                    recipe=obj).exists()
                )


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Ингредиент и количество для создания рецепта."""
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = (
            'id',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Список рецептов без ингридиентов."""
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )



class RecipeCreateSerializer(serializers.ModelSerializer):
    """Создание, изменение и удаление рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    author = UserCreateSerializer(read_only=True)
    id = serializers.ReadOnlyField()
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate(self, obj):
        if not obj.get('tags'):
            raise serializers.ValidationError(
                'Укажите минимум 1 тег.'
            )
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Нужно минимум 1 ингредиент.'
            )
        return obj

    def create_ingredients_and_tags(self, recipe, tags, ingredients):
        for tag in tags:
            recipe.tags.add(tag)
            recipe.save()
        for ingredient in ingredients:
            RecipeIngredients.objects.create(
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
                recipe=recipe
            )
        return recipe

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients_and_tags(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        return self.create_ingredients_and_tags(
            instance, tags, ingredients
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context=self.context
        ).data
class ShoppingCartSerializer(RecipeSerializer):
    """Сериализатор добавления рецепта в корзину"""
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()

    class Meta(RecipeSerializer.Meta):
        fields = ("id", "name", "image", "cooking_time")

    def validate(self, data):
        recipe = self.instance
        user = self.context.get('request').user
        if ShoppingCartList.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                detail='Рецепт уже добавлен в корзину',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data