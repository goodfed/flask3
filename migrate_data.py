import json

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import data

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/tinysteps.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

teachers_goals_association = db.Table(
    'teachers_goals',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id')),
    db.Column('goal_id', db.Integer, db.ForeignKey('goals.id'))
)


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    about = db.Column(db.Text(500))
    rating = db.Column(db.Float)
    picture = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    goals = db.relationship(
        'Goal', secondary=teachers_goals_association, back_populates='teachers'
    )
    free = db.Column(db.Text)
    bookings = db.relationship('Booking', back_populates='teacher')


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    teacher = db.relationship('Teacher', back_populates='bookings')
    weekday = db.relationship('Weekday', back_populates='bookings')
    weekday_id = db.Column(db.Integer, db.ForeignKey('weekdays.id'))
    time = db.Column(db.String(5), nullable=False)
    client_name = db.Column(db.String(50), nullable=False)
    client_phone = db.Column(db.String(12), nullable=False)


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'))
    goal = db.relationship('Goal', back_populates='requests')
    time = db.Column(db.String(5), nullable=False)
    client_name = db.Column(db.String(50), nullable=False)
    client_phone = db.Column(db.String(12), nullable=False)


class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(25), nullable=False, unique=True)
    name = db.Column(db.String(25), nullable=False)
    emoji = db.Column(db.String(5), nullable=False)
    teachers = db.relationship(
        'Teacher', secondary=teachers_goals_association, back_populates='goals'
    )
    requests = db.relationship('Request', back_populates='goal')


class Weekday(db.Model):
    __tablename__ = 'weekdays'
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(3), nullable=False, unique=True)
    name = db.Column(db.String(15), nullable=False)
    bookings = db.relationship('Booking', back_populates='weekday')


db.create_all()


weekdays = {
    "mon": "Понедельник",
    "tue": "Вторник",
    "wed": "Среда",
    "thu": "Четверг",
    "fri": "Пятница",
    "sat": "Суббота",
    "sun": "Воскресенье"
}

goals = [
    {"alias": "travel", "name": "Для путешествий", "emoji": "⛱"},
    {"alias": "study", "name": "Для учебы", "emoji": "🏫"},
    {"alias": "work", "name": "Для работы", "emoji": "🏢"},
    {"alias": "relocate", "name": "Для переезда", "emoji": "🚜"},
    {"alias": "prog", "name": "Для программирования", "emoji": "🐱"}
]

for goal in goals:
    new_goal = Goal(alias=goal['alias'], name=goal['name'], emoji=goal['emoji'])
    db.session.add(new_goal)

for day in weekdays:
    new_day = Weekday(alias=day, name=weekdays[day])
    db.session.add(new_day)

for teacher in data.teachers:
    goals_list = []
    for goal in teacher['goals']:
        goal_item = db.session.query(Goal).filter(Goal.alias == goal).first()
        goals_list.append(goal_item)

    new_teacher = Teacher(
        name = teacher['name'],
        about = teacher['about'],
        rating = teacher['rating'],
        picture = teacher['picture'],
        price = teacher['price'],
        goals = goals_list,
        free = json.dumps(teacher['free'])
    )

    db.session.add(new_teacher)

db.session.commit()