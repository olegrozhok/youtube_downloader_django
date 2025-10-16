<div align="center">

# 🎬 YouTube Downloader (Django + yt-dlp)

⚡ Простое веб-приложение на **Django**, позволяющее скачивать видео с YouTube  
с отображением **прогресса загрузки** и **выбором разрешения**.

![screenshot](https://raw.githubusercontent.com/olegrozhok/youtube_downloader_django/main/demo/screenshot.png)

</div>

---

## 🚀 Функционал

✅ Вставь ссылку на YouTube  
✅ Просмотри доступные форматы и разрешения  
✅ Отслеживай прогресс загрузки в реальном времени  
✅ Автоматическое объединение видео + звука  
✅ Кроссплатформенность (Windows / Linux / macOS)

---

## 🛠️ Установка и запуск

```bash
# 1️⃣ Клонируем репозиторий
git clone https://github.com/olegrozhok/youtube_downloader_django.git
cd youtube_downloader_django

# 2️⃣ Создаем виртуальное окружение
python -m venv venv
venv\Scripts\activate   # (или source venv/bin/activate на Linux/Mac)

# 3️⃣ Устанавливаем зависимости
pip install -r requirements.txt

# 4️⃣ Запускаем сервер
python manage.py runserver
```

## 📦 Зависимости

| Библиотека | Назначение                |
| ---------- | ------------------------- |
| `Django`   | Веб-фреймворк             |
| `yt-dlp`   | Загрузка видео с YouTube  |
| `ffmpeg`   | Объединение видео и звука |

## ⚙️ Требования

* Python 3.10+

* Django 4+

* Установленный ffmpeg (должен быть доступен в PATH)

Проверить установку ffmpeg:

```bash
ffmpeg -version
```

## 💡 Возможные улучшения

1. [ ]  Добавить очередь загрузок
3. [ ]  Авторизация пользователей
5. [ ]  История скачанных видео
7. [ ]  Поддержка загрузки плейлистов