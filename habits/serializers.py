from rest_framework import serializers

from habits.models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = ("user",)

    def validate(self, attrs):
        instance = self.instance

        is_pleasant = attrs.get(
            "is_pleasant",
            getattr(instance, "is_pleasant", False),
        )
        reward = attrs.get(
            "reward",
            getattr(instance, "reward", ""),
        )
        related_habit = attrs.get(
            "related_habit",
            getattr(instance, "related_habit", None),
        )
        execution_time = attrs.get(
            "execution_time",
            getattr(instance, "execution_time", 60),
        )
        frequency = attrs.get(
            "frequency",
            getattr(instance, "frequency", 1),
        )

        if reward and related_habit:
            raise serializers.ValidationError(
                "Укажи либо вознаграждение, либо связанную привычку."
            )

        if related_habit and not related_habit.is_pleasant:
            raise serializers.ValidationError(
                "Связанная привычка должна быть приятной."
            )

        if is_pleasant and (reward or related_habit):
            raise serializers.ValidationError(
                "У приятной привычки не может быть награды " "или связанной привычки."
            )

        if execution_time > 120:
            raise serializers.ValidationError(
                {"execution_time": "Максимум 120 секунд."}
            )

        if not 1 <= frequency <= 7:
            raise serializers.ValidationError(
                {"frequency": "Периодичность должна быть от 1 до 7 дней."}
            )

        return attrs
