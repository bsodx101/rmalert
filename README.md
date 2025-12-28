# RMAlert — Redmine to Telegram Alert Bot

RMAlert is a lightweight Python bot that monitors **Redmine issues** using a saved query and sends **Telegram notifications** when new issues appear.

It is designed for teams who need near real-time alerts about **high-priority or critical issues** without constantly checking Redmine.

---

## 🚀 Features

- 🔍 Fetches issues from Redmine via **saved query (`query_id`)**
- 🆕 Detects **new issues only** (no duplicates)
- ⚠️ Filters issues by priority (IDs 1–4)
- 👤 Detects who last changed the `assigned_to` field
- 📬 Sends formatted alerts to Telegram
- 🧾 MarkdownV2-safe messages (automatic escaping)
- 🔁 Runs continuously with configurable polling interval

---

## 🧠 How It Works

1. Periodically requests issues from Redmine using the REST API
2. Filters issues by priority
3. Compares current issues with previously seen ones
4. When new issues appear:
   - Collects issue metadata
   - Resolves the last user who assigned the task
   - Sends a Telegram notification
5. Sleeps and repeats

---

## 🛠 Tech Stack

- Python 3.9+
- `asyncio`
- `requests`
- `aiogram`
- Redmine REST API
- Telegram Bot API

---
