from http import HTTPStatus

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .pdf_download import pdf_download
from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination, CustomPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavouriteSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeReadSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    SubscribeSerializer,
    SubscriptionSerializer,
    UserSerializer,
)
from recipes.models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCartList,
    Tag,
)
from users.models import Subscribe, User


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ("^name",)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет тэгов только для просмотра."""

    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all().select_related(
        "author"
    ).prefetch_related(
        "tags",
        "ingredients"
    )
    pagination_class = PageLimitPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = (
        "delete",
        "post",
        "get",
        "create",
        "patch",
    )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @staticmethod
    def favorite_shopping_cart(serializers, request, pk):
        context = {"request": request}
        data = {"user": request.user.id, "recipe": pk}
        serializer = serializers(
            data=data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(
        detail=True,
        methods=("post",),
        url_path="favorite",
        url_name="favorite",
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.favorite_shopping_cart(
            FavouriteSerializer,
            request,
            pk
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        favourite = Favourite.objects.filter(
            user=request.user, recipe_id=pk
        )
        if favourite.exists():
            favourite.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(status=HTTPStatus.BAD_REQUEST)

    @action(
        detail=True,
        methods=("post",),
        url_path="shopping_cart",
        url_name="shopping_cart",
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.favorite_shopping_cart(
            ShoppingCartSerializer,
            request,
            pk
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        shopping_cart = ShoppingCartList.objects.filter(
            user=request.user, recipe_id=pk
        )
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(status=HTTPStatus.BAD_REQUEST)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            RecipeIngredients.objects.filter(
                recipe__shopping_recipe__user=request.user
            )
            .values("ingredient")
            .annotate(total_amount=Sum("amount")).order_by(
                "ingredient__name"
            )
            .values_list(
                "ingredient__name",
                "total_amount",
                "ingredient__measurement_unit"
            )
        )
        return pdf_download(ingredients)


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для модели User и Subscribe."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action == "me":
            return (IsAuthenticated(), )
        return super().get_permissions()

    @action(
        detail=False,
        url_path="subscriptions",
        url_name="subscriptions",
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        queryset = User.objects.filter(author__user=self.request.user)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(
            queryset, request, view=self
        )
        serializer = SubscriptionSerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=("post",),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        """Метод для создания подписки."""
        data = {"user": request.user.id, "author": id}
        serializer = SubscribeSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        subscription = Subscribe.objects.filter(
            user=request.user, author_id=id
        )
        if subscription.exists():
            subscription.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(status=HTTPStatus.BAD_REQUEST)
