import logging
from datetime import timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from habits.models import Habit

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id, text):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("ok", False)
    except requests.RequestException:
        logger.exception("Failed to send Telegram message")
        return False


@shared_task
def send_habit_reminders():
    now = timezone.localtime()
    today = now.date()

    habits = Habit.objects.filter(
        time__hour=now.hour,
        time__minute=now.minute,
        user__telegram_chat_id__isnull=False,
    ).select_related("user", "related_habit")

    sent = 0

    for habit in habits:
        days_passed = (today - habit.created_at.date()).days

        if days_passed < 0 or days_passed % habit.frequency != 0:
            continue

        message = (
            f"Напоминание о привычке!\n"
            f"Действие: {habit.action}\n"
            f"Место: {habit.place}\n"
            f"Время: {habit.time.strftime('%H:%M')}"
        )

        if send_telegram_message(
            habit.user.telegram_chat_id,
            message,
        ):
            sent += 1

    return sent
