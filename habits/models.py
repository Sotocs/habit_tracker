
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Пользователь",
    )
    place = models.CharField(
        max_length=255,
        verbose_name="Место выполнения",
    )
    time = models.TimeField(
        verbose_name="Время выполнения",
    )
    action = models.CharField(
        max_length=255,
        verbose_name="Действие",
    )
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name="Приятная привычка",
    )
    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rewarded_habits",
        verbose_name="Связанная привычка",
    )
    frequency = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(7),
        ],
        verbose_name="Периодичность в днях",
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Вознаграждение",
    )
    execution_time = models.PositiveSmallIntegerField(
        default=60,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(120),
        ],
        verbose_name="Время выполнения в секундах",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Публичная привычка",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    def clean(self):
        super().clean()
        errors = {}

        if self.reward and self.related_habit_id:
            errors["reward"] = (
                "Нельзя одновременно указать вознаграждение "
                "и связанную привычку."
            )

        if self.related_habit_id and not self.related_habit.is_pleasant:
            errors["related_habit"] = (
                "Связанная привычка должна быть приятной."
            )

        if self.is_pleasant and self.reward:
            errors["reward"] = (
                "У приятной привычки не может быть вознаграждения."
            )

        if self.is_pleasant and self.related_habit_id:
            errors["related_habit"] = (
                "У приятной привычки не может быть связанной привычки."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.action

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["time", "id"]

