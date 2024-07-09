from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Кастомная проверка разрешений на уровне объекта.
    Проверяет на авторство и аутентифицированность пользователя
    отправляющего запрос.
    """

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
