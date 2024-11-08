import asyncio
import requests
import re
import os
from aiogram import Bot
from telegram.error import TelegramError

# Инициализация бота
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)

# Настройки бота
API_KEY = os.getenv("API_KEY")  
CHAT_ID = os.getenv("CHAT_ID")  
REDMINE_URL = os.getenv("REDMINE_URL") 
CHECK_INTERVAL = 180  
QUERY_ID = 2015 


def escape_markdown_v2(text):
    """Экранируем спецсимвлы """
    return re.sub(r'([_*.\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


def priority_to_text(priority_id):
    """ID приоритета > текст."""
    if priority_id == 3:
        return "⚠️Высокий"
    elif priority_id == 4:
        return "🚨КРИТИЧЕСКИЙ🚨"
    return "Cущественный"


# Функция для получения задач с фильтром по query_id
def get_issues(query_id):
    url = f'{REDMINE_URL}/issues.json?query_id={query_id}'
    headers = {
        'X-Redmine-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Получены задачи: {response.json()}")  # Логгируем полученные данные
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении задач: {e}")
        return None


# Функция для получения последнего пользователя, который изменил параметр assigned_to
def get_last_assigned_user(issue_id):
    url = f'{REDMINE_URL}/issues/{issue_id}.json?include=journals'
    headers = {
        'X-Redmine-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        journals = response.json().get('issue', {}).get('journals', [])

        for journal in reversed(journals):  # Идем desc
            for detail in journal.get('details', []):
                if detail.get('property') == 'attr' and detail.get('name') == 'assigned_to_id':
                    return journal.get('user', {}).get('name', 'Неизвестный пользователь')
        return ""
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении журнала для задачи {issue_id}: {e}")
        return "автор "


# Функция для извлечения задач if priority_id in [1, 2, 3, 4]
def parse_issues(data):
    issues = []
    total_count = data['total_count']  # Получаем общее количество задач
    for issue in data['issues']:
        priority_id = issue['priority']['id']
        subject = issue['subject']
        status = issue['status']['name']
        project = issue['project']['name']
        issue_id = issue['id']
        issue_url = f'{REDMINE_URL}/issues/{issue_id}'
        author = issue.get('author', {}).get('name', 'Неизвестный автор')  # Получаем имя автора

        if priority_id in [1, 2, 3, 4]: # можно выбирать только высокий или крит
            issues.append({
                'id': issue_id,
                'subject': subject,
                'priority_id': priority_id,
                'status': status,
                'project': project,
                'url': issue_url,
                'author': author
            })
    print(f"Отфильтрованные задачи: {issues}")
    return issues, total_count


# Функция для отправки
async def send_telegram_message(message):
    try:
        message = escape_markdown_v2(message)  # Экранируем текст перед отправкой
        print(f"Отправка сообщения: {message}")  # Логирование отправляемого сообщения
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='MarkdownV2')
        print("Сообщение успешно отправлено.")
    except TelegramError as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")


# функция для отслеживания изменений
async def track_page():
    last_issues = []  # Храним предыдущее состояние задач

    while True:
        data = get_issues(QUERY_ID)
        if data:
            current_issues, total_count = parse_issues(data)

            new_issues = [issue for issue in current_issues if issue not in last_issues]
            if new_issues:
                message = "Новая задача на !HELPDESK:\n"
                for issue in new_issues:
                    # Получаем имя последнего пользователя, изменившего assigned_to
                    last_assigned_user = get_last_assigned_user(issue['id'])
                    message += (
                        f"Проект: {issue['project']}\n"
                        f"Тема: {issue['subject']}\n"
                        f"Приоритет: {priority_to_text(issue['priority_id'])}\n"
                        f"Статус: {issue['status']}\n"
                        f"Автор: {issue['author']}\n"  
                        f"Назначил(а): {last_assigned_user}\n"
                        f"🍏 {issue['url']}\n\n"
                    )
                # тотал
                message += f"Всего задач 👉🏻{total_count}👈🏻"

                await send_telegram_message(message)
                last_issues.extend(new_issues)  # Обновляем список последних задач
            else:
                print("Изменений не обнаружено.")

        await asyncio.sleep(CHECK_INTERVAL)  # Задержка перед следующей проверкой


if __name__ == '__main__':
    asyncio.run(track_page())
