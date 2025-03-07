# HabitMinder 🚀 — Ваш персональный трекер привычек

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Превратите свои цели в привычки** с умным трекером, который помогает сохранять мотивацию и отслеживать прогресс!

<div align="center">
  <img src="https://via.placeholder.com/800x400.png?text=HabitMinder+Dashboard+Preview" alt="Демо интерфейса">
</div>

## 🌟 Ключевые возможности
✅ **Персонализированный трекинг**  
- Создавайте привычки с гибкой периодичностью (ежедневно/еженедельно/ежемесячно)  
- Визуализация прогресса через интерактивный календарь  

🔒 **Безопасный аккаунт**  
- Шифрование паролей с помощью bcrypt  
- Сессии с запоминанием устройства  

📊 **Умная аналитика**  
- Автоматическое формирование статистики  
- Экспорт данных в JSON  

📲 **Адаптивный интерфейс**  
- Полная мобильная поддержка  
- Material Design элементы  

## 🛠 Технологический стек
| Компонент      | Технологии                          |
|----------------|-------------------------------------|
| **Backend**    | Flask, SQLAlchemy, Flask-Login      |
| **Frontend**   | Jinja2, HTML5, CSS3                 |
| **База данных**| PostgreSQL/SQLite                   |
| **Безопасность**| Werkzeug, CSRF-токены              |

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- PostgreSQL или SQLite

### Установка за 3 шага
```bash
# 1. Клонировать репозиторий
git clone https://github.com/LeoTechRu/habitminder.git
cd habitminder

# 2. Настроить окружение
echo "DATABASE_URL=postgresql:///habitminder" > .env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env

# 3. Запустить
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run
```

## 📈 Пример использования
```python
# Создание новой привычки
new_habit = Habit(
    title="Ежедневная зарядка",
    frequency="daily",
    progress={'2025-03-01': True, '2025-03-02': False}
)
```
## 📌 Почему HabitMinder?
Особенность	Преимущество
Гибкость	Поддержка любой периодичности привычек
Конфиденциальность	Локальное хранение данных
Мотивация	Визуализация цепочки успехов
Открытый код	Возможность кастомизации
## 🌍 Roadmap 2025
 Мобильное приложение (Flutter)
 Интеграция с Google Calendar
 Система достижений
 Социальный шаринг прогресса
## 🤝 Как можно помочь проекту
Тестирование и сообщения об ошибках
Перевод документации
Разработка новых модулей
Присоединяйтесь к сообществу HabitMinder!

## 🌱 Начните свой путь к лучшей версии себя уже сегодня!

## 💡 Идеи и предложения: leotechru@ya.ru
