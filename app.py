# /sd/habitminder/app.py
from datetime import datetime, timedelta
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
    
    # Конфигурация
    app.config.from_prefixed_env()
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    
    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Настройка Flask-Login
    login_manager.login_view = 'login'
    
    # Регистрация моделей
    with app.app_context():
        db.create_all()
    
    # Регистрация blueprints/роутов
    #from . import routes
    #app.register_blueprint(routes.bp)
    
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

# Forms
from flask_wtf import FlaskForm

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Обязательное поле"),
        Email(message="Некорректный email-адрес")
    ])
    
    password = PasswordField('Пароль', validators=[
        DataRequired(message="Введите пароль"),
        Length(min=8, max=64, 
              message="Пароль должен содержать от 8 до 64 символов")
    ])
    
    confirm = PasswordField('Повторите пароль', validators=[
        DataRequired(message="Подтвердите пароль"),
        EqualTo('password', message="Пароли должны совпадать")
    ])

class HabitForm(FlaskForm):
    title = StringField('Habit Title', validators=[DataRequired()])
    frequency = SelectField('Frequency', choices=[
        ('daily', 'Daily'), 
        ('weekly', 'Weekly'), 
        ('monthly', 'Monthly')
    ])

# Routes
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
        flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm.data:
            flash('Passwords must match')
            return redirect(url_for('register'))
        
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
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
        flash('Habit created successfully')
        return redirect(url_for('dashboard'))
    return render_template('create_habit.html', form=form)

@app.route('/habit/<int:habit_id>/update', methods=['POST'])
@login_required
def update_habit(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    date = request.form['date']
    status = request.form.get('status', 'false') == 'true'
    
    progress = habit.progress or {}
    progress[date] = status
    habit.progress = progress
    
    db.session.commit()
    return {'status': 'success'}

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 3001))