from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrPublicReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return obj.user == request.user or obj.is_public

        return obj.user == request.user