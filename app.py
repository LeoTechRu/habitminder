from datetime import datetime, timedelta, date as dt_date
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
import os
import json
import logging
from dotenv import load_dotenv
load_dotenv()  # Загрузка переменных окружения

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Конфигурация приложения
    app.config.from_prefixed_env()
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'),
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Настройка аутентификации
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    # Пользовательские фильтры Jinja2
    def ru_frequency(freq):
        frequency_map = {
            'daily': 'Ежедневно',
            'weekly': 'Еженедельно', 
            'monthly': 'Ежемесячно'
        }
        return frequency_map.get(freq, freq)
    
    def format_tooltip(date_str, habit):
        try:
            date_obj = dt_date.fromisoformat(date_str)
            status_map = {
                'completed': '✅ Выполнено',
                'missed': '❌ Пропущено',
                'current': '🕒 Сегодня'
            }
            return f"{date_obj.strftime('%d %B %Y')}\n{status_map.get(habit.progress.get(date_str, 'current'))}"
        except ValueError:
            return "Неверный формат даты"

    app.jinja_env.filters.update({
        'ru_frequency': ru_frequency,
        'format_tooltip': format_tooltip
    })

    # Контекстные процессоры
    @app.context_processor
    def inject_utilities():
        def generate_calendar(habit):
            today = dt_date.today()
            start_date = max(
                habit.created_at.date(),
                today - timedelta(days=14)  # Показываем 2 недели назад от текущей даты
            )
        
            calendar_days = []
            for i in range(30):  # Всего 30 дней в календаре
                current_date = start_date + timedelta(days=i)
                status = 'future' if current_date > today else (
                    'completed' if habit.progress.get(current_date.isoformat(), False)
                    else 'current' if current_date == today
                    else 'missed'
                )
                calendar_days.append((current_date.isoformat(), status))
            return calendar_days

        def is_future_date(date_str):
            try:
                return dt_date.fromisoformat(date_str) > dt_date.today()
            except ValueError:
                return False

        return {
            'generate_calendar': generate_calendar,
            'is_future_date': is_future_date,
            'timedelta': timedelta,
            'current_year': datetime.utcnow().year
        }

    # Инициализация базы данных
    with app.app_context():
        db.create_all()
        # Пример добавления начальных данных
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(email='admin@example.com')
            admin.set_password('securepassword')
            db.session.add(admin)
            db.session.commit()
            logging.info("Создан администратор с email: admin@example.com")

    return app

# Модели
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(256))
    habits = db.relationship('Habit', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    frequency = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.JSON, default=dict)  # Исправлено на dict
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def reset_progress(self):
        self.progress = {}
        self.created_at = datetime.utcnow()

# Фабрика приложения
app = create_app()

# Инициализация Flask-Login
@login_manager.user_loader
def load_user(user_id):
    logging.debug(f"Загрузка пользователя с ID: {user_id}")
    return User.query.get(int(user_id))

# Формы
from flask_wtf import FlaskForm

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Обязательное поле"),
        Email(message="Некорректный email")
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message="Введите пароль")
    ])
    remember = BooleanField('Запомнить меня')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Обязательное поле"),
        Email(message="Некорректный email")
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message="Введите пароль"),
        Length(min=8, max=64, message="Пароль должен быть от 8 до 64 символов")
    ])
    confirm = PasswordField('Повторите пароль', validators=[
        DataRequired(message="Подтвердите пароль"),
        EqualTo('password', message="Пароли не совпадают")
    ])

class HabitForm(FlaskForm):
    title = StringField('Название привычки', validators=[
        DataRequired(message="Введите название")
    ])
    frequency = SelectField('Периодичность', choices=[
        ('daily', 'Ежедневно'), 
        ('weekly', 'Еженедельно'), 
        ('monthly', 'Ежемесячно')
    ])

# Роуты
@app.route('/')
def index():
    logging.debug("Загрузка главной страницы")
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.debug("Попытка входа")
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            logging.info(f"Пользователь {form.email.data} успешно вошел в систему")
            return redirect(url_for('dashboard'))
        flash('Неверный email или пароль', 'error')
        logging.warning(f"Неверный вход для email: {form.email.data}")
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    logging.debug("Попытка регистрации")
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Этот email уже зарегистрирован', 'error')
            return redirect(url_for('register'))
        
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь войдите в систему', 'success')
        logging.info(f"Пользователь {form.email.data} зарегистрирован")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    logging.debug("Загрузка страницы dashboard")
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    
    total_days = 30  # Установите количество дней, которое вы хотите отображать

    for habit in habits:
        logging.debug(f"Habit {habit.id}: Progress values: {list(habit.progress.values())}, Total days: {len(habit.progress.values())}")
    
    return render_template('dashboard.html', habits=habits, total_days=total_days)

@app.route('/habit/create', methods=['GET', 'POST'])
@login_required
def create_habit():
    logging.debug("Попытка создания привычки")
    form = HabitForm()
    if form.validate_on_submit():
        try:
            habit = Habit(
                title=form.title.data,
                frequency=form.frequency.data,
                user_id=current_user.id
            )
            db.session.add(habit)
            db.session.commit()
            flash('Привычка успешно создана', 'success')
            logging.info(f"Привычка '{habit.title}' успешно создана пользователем {current_user.email}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Ошибка при создании привычки: {str(e)}', 'error')
            logging.error(f'Ошибка при создании привычки: {str(e)}')
    return render_template('create_habit.html', form=form)

@app.route('/habit/<int:habit_id>/update', methods=['POST'])
@login_required
def update_habit(habit_id):
    """Обработчик обновления статуса привычки"""
    logging.debug(f"Попытка обновления привычки с ID: {habit_id}")
    habit = Habit.query.get_or_404(habit_id)
    
    # Проверка прав доступа
    if habit.user_id != current_user.id:
        logging.warning(f"Неавторизованный доступ к привычке {habit_id} от {current_user.email}")
        return jsonify({'status': 'error', 'message': 'Доступ запрещен'}), 403

    try:
        # Обработка разных типов запросов
        if request.is_json:
            data = request.get_json()
            date_str = data.get('date')
        else:  # Для форм-данных
            date_str = request.form.get('date')

        # Валидация формата даты
        if not isinstance(date_str, str) or len(date_str) != 10:
            raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")

        # Преобразование даты
        date_obj = dt_date.fromisoformat(date_str)
        today = dt_date.today()
        
        # Проверка допустимости даты
        if date_obj != today:
            logging.warning(f"Попытка изменения не текущей даты: {date_str}")
            return jsonify({
                'status': 'error',
                'message': 'Можно изменять только текущий день'
            }), 400
            
        if date_obj < habit.created_at.date():
            logging.warning(f"Дата {date_str} раньше создания привычки")
            return jsonify({
                'status': 'error',
                'message': 'Нельзя изменять исторические данные'
            }), 400

        # Обновление прогресса
        progress = habit.progress.copy() or {}
        current_status = progress.get(date_str, False)
        progress[date_str] = not current_status
        
        # Сохранение изменений
        habit.progress = progress
        db.session.commit()
        
        logging.info(f"Обновлен статус привычки {habit_id} за {date_str}")
        return jsonify({
            'status': 'success',
            'new_status': progress[date_str],
            'completed_days': sum(1 for v in progress.values() if v),
            'total_days': len(progress)
        })
        
    except ValueError as e:
        logging.error(f'Ошибка валидации: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'Ошибка формата данных: {str(e)}'
        }), 400
    except Exception as e:
        logging.error(f'Критическая ошибка обновления: {str(e)}')
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Внутренняя ошибка сервера: ' + str(e)
        }), 500

@app.route('/habit/<int:habit_id>/update_meta', methods=['POST'])
@login_required
def update_habit_meta(habit_id):
    """Обновление метаданных привычки"""
    habit = Habit.query.get_or_404(habit_id)
    
    if habit.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Доступ запрещен'}), 403

    try:
        # Обновление только названия
        new_title = request.form.get('title')
        if new_title and new_title != habit.title:
            habit.title = new_title
            db.session.commit()
            flash('Название успешно обновлено', 'success')
        
        return redirect(url_for('dashboard'))

    except Exception as e:
        db.session.rollback()
        logging.error(f'Ошибка обновления: {str(e)}')
        flash('Ошибка при обновлении привычки', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/habit/<int:habit_id>/delete', methods=['DELETE'])
@login_required
def delete_habit(habit_id):
    logging.debug(f"Попытка удаления привычки с ID: {habit_id}")
    habit = Habit.query.get_or_404(habit_id)
    if habit.user_id != current_user.id:
        logging.warning(f"Попытка удаления привычки {habit_id} пользователем {current_user.email}, у которого нет прав")
        return {'status': 'error', 'message': 'Нет прав для удаления'}, 403
    
    db.session.delete(habit)
    db.session.commit()
    logging.info(f"Привычка {habit_id} успешно удалена пользователем {current_user.email}")
    return {'status': 'success'}

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    logging.info(f"Пользователь {current_user.email} вышел из системы")
    return redirect(url_for('index'))

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=os.environ.get('PORT', 3001))