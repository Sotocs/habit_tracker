from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from habits.models import Habit
from rest_framework.test import APITestCase

User = get_user_model()


class HabitPermissionTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="habit_owner",
            password="test-password-123",
        )
        self.other_user = User.objects.create_user(
            username="other_user",
            password="test-password-123",
        )

        self.private_habit = Habit.objects.create(
            user=self.owner,
            place="Дом",
            time=time(9, 0),
            action="Прочитать книгу",
        )
        self.public_habit = Habit.objects.create(
            user=self.owner,
            place="Парк",
            time=time(10, 0),
            action="Погулять",
            is_public=True,
        )

    def get_detail_url(self, habit):
        return f"/api/habits/{habit.pk}/"

    def test_anonymous_user_can_view_public_habit(self):
        response = self.client.get(self.get_detail_url(self.public_habit))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_cannot_view_private_habit(self):
        response = self.client.get(self.get_detail_url(self.private_habit))

        self.assertEqual(response.status_code, 404)

    def test_owner_can_update_own_habit(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            self.get_detail_url(self.private_habit),
            {"action": "Прочитать две страницы"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.private_habit.refresh_from_db()
        self.assertEqual(
            self.private_habit.action,
            "Прочитать две страницы",
        )

    def test_other_user_cannot_update_public_habit(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            self.get_detail_url(self.public_habit),
            {"action": "Изменённое действие"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_view_private_habit(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self.get_detail_url(self.private_habit))

        self.assertEqual(response.status_code, 404)


class HabitModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user",
            password="test-password-123",
        )

    def create_habit(self, **kwargs):
        data = {
            "user": self.user,
            "place": "Дом",
            "time": time(9, 0),
            "action": "Прочитать одну страницу",
            "execution_time": 60,
            "frequency": 1,
        }
        data.update(kwargs)
        return Habit(**data)

    def test_habit_creation(self):
        habit = self.create_habit()
        habit.full_clean()
        habit.save()

        self.assertEqual(Habit.objects.count(), 1)
        self.assertEqual(str(habit), "Прочитать одну страницу")

    def test_execution_time_cannot_exceed_120_seconds(self):
        habit = self.create_habit(execution_time=121)

        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_frequency_cannot_exceed_seven_days(self):
        habit = self.create_habit(frequency=8)

        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_reward_and_related_habit_cannot_be_set_together(self):
        pleasant = self.create_habit(
            action="Послушать музыку",
            is_pleasant=True,
        )
        pleasant.full_clean()
        pleasant.save()

        habit = self.create_habit(
            reward="Чашка чая",
            related_habit=pleasant,
        )

        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_related_habit_must_be_pleasant(self):
        ordinary = self.create_habit()
        ordinary.full_clean()
        ordinary.save()

        habit = self.create_habit(related_habit=ordinary)

        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_pleasant_habit_cannot_have_reward(self):
        habit = self.create_habit(
            is_pleasant=True,
            reward="Чашка чая",
        )

        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_pleasant_habit_cannot_have_related_habit(self):
        pleasant = self.create_habit(
            action="Послушать музыку",
            is_pleasant=True,
        )
        pleasant.full_clean()
        pleasant.save()

        habit = self.create_habit(
            is_pleasant=True,
            related_habit=pleasant,
        )

        with self.assertRaises(ValidationError):
            habit.full_clean()


from rest_framework.test import APITestCase
from habits.serializers import HabitSerializer


class HabitSerializerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="serializer_user",
            password="test-password-123",
        )
        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Дома",
            time="08:00",
            action="Послушать любимую музыку",
            is_pleasant=True,
        )
        self.valid_data = {
            "place": "Дома",
            "time": "09:00",
            "action": "Прочитать книгу",
            "is_pleasant": False,
            "frequency": 1,
            "execution_time": 60,
            "reward": "",
            "related_habit": None,
            "is_public": False,
        }

    def test_valid_habit(self):
        serializer = HabitSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_reward_and_related_habit_are_mutually_exclusive(self):
        data = {
            **self.valid_data,
            "reward": "Посмотреть сериал",
            "related_habit": self.pleasant_habit.pk,
        }
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_related_habit_must_be_pleasant(self):
        ordinary_habit = Habit.objects.create(
            user=self.user,
            place="Дома",
            time="10:00",
            action="Убрать стол",
        )
        data = {
            **self.valid_data,
            "related_habit": ordinary_habit.pk,
        }
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_pleasant_habit_cannot_have_reward(self):
        data = {
            **self.valid_data,
            "is_pleasant": True,
            "reward": "Посмотреть сериал",
        }
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_pleasant_habit_cannot_have_related_habit(self):
        data = {
            **self.valid_data,
            "is_pleasant": True,
            "related_habit": self.pleasant_habit.pk,
        }
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_execution_time_cannot_exceed_120_seconds(self):
        data = {**self.valid_data, "execution_time": 121}
        serializer = HabitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_frequency_must_be_between_one_and_seven(self):
        for frequency in (0, 8):
            with self.subTest(frequency=frequency):
                data = {**self.valid_data, "frequency": frequency}
                serializer = HabitSerializer(data=data)
                self.assertFalse(serializer.is_valid())
