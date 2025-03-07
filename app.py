# /sd/habitminder/app.py
from datetime import datetime, timedelta, date as dt_date
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
import os
import json

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
            status = 'Выполнено' if habit.progress.get(date_str) else 'Пропущено'
            return f"{date_obj.strftime('%d %B %Y')}\nСтатус: {status}"
        except (ValueError, KeyError):
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
            return [
                (
                    (habit.created_at.date() + timedelta(days=i)).isoformat(),
                    'future' if (habit.created_at.date() + timedelta(days=i)) > today
                    else 'completed' if habit.progress.get((habit.created_at.date() + timedelta(days=i)).isoformat(), False)
                    else 'missed'
                ) for i in range(30)
            ]

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
    progress = db.Column(db.JSON, default={})
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Фабрика приложения
app = create_app()

# Инициализация Flask-Login
@login_manager.user_loader
def load_user(user_id):
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
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        flash('Неверный email или пароль', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
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
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    habits = current_user.habits.all()
    return render_template('dashboard.html', habits=habits)

@app.route('/habit/create', methods=['GET', 'POST'])
@login_required
def create_habit():
    form = HabitForm()
    if form.validate_on_submit():
        habit = Habit(
            title=form.title.data,
            frequency=form.frequency.data,
            user_id=current_user.id
        )
        db.session.add(habit)
        db.session.commit()
        flash('Привычка успешно создана', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_habit.html', form=form)

@app.route('/habit/<int:habit_id>/update', methods=['POST'])
@login_required
def update_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    date_str = request.form['date']
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        if date_obj > datetime.utcnow().date():
            return {'status': 'error', 'message': 'Нельзя отмечать будущие даты'}, 400
            
        progress = habit.progress or {}
        current_status = progress.get(date_str, False)
        progress[date_str] = not current_status
        
        habit.progress = progress
        db.session.commit()
        
        return {'status': 'success', 'new_status': progress[date_str]}
    except ValueError:
        return {'status': 'error', 'message': 'Неверный формат даты'}, 400

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 3001))