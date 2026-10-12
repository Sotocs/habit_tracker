from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from habits.models import Habit
from habits.permissions import IsOwnerOrPublicReadOnly
from habits.serializers import HabitSerializer
from django.db import models


class HabitListCreateView(generics.ListCreateAPIView):
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    serializer_class = HabitSerializer
    permission_classes = [AllowAny]
    queryset = Habit.objects.filter(is_public=True)


class HabitDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HabitSerializer
    permission_classes = [IsOwnerOrPublicReadOnly]

    def get_queryset(self):
        queryset = Habit.objects.filter(is_public=True)

        if self.request.user.is_authenticated:
            queryset = queryset | Habit.objects.filter(
                user=self.request.user
            )

        return queryset