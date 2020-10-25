import json

from flask import Flask, render_template, abort, request
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, RadioField, SubmitField, validators
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/tinysteps.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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


goals_select = []
goals = db.session.query(Goal).all()
for goal in goals:
    goals_select.append((goal.alias, goal.name))


weekdays = db.session.query(Weekday).all()
days = {}
for day in weekdays:
    days[day.alias] = day.name


class BookingForm(FlaskForm):
    clientWeekday = HiddenField('День недели', validators=[validators.InputRequired()])
    clientTime = HiddenField('Время', validators=[validators.InputRequired()])
    clientTeacher = HiddenField('Учитель', validators=[validators.InputRequired()])
    clientName = StringField('Вас зовут', validators=[validators.InputRequired(), validators.Length(max=50)])
    clientPhone = StringField('Ваш телефон', validators=[validators.InputRequired(), validators.Length(max=12)])
    submit = SubmitField('Записаться на пробный урок')


class RequestForm(FlaskForm):
    goal = RadioField('Какая цель занятий?', choices=goals_select, default=goals_select[0][0], validators=[validators.InputRequired()])
    time = RadioField('Сколько времени есть?', choices=[
        ('1-2', '1-2 часа в неделю'),
        ('3-5', '3-5 часов в неделю'),
        ('5-7', '5-7 часов в неделю'),
        ('7-10', '7-10 часов в неделю')
    ], default='1-2', validators=[validators.InputRequired()])
    clientName = StringField('Вас зовут', validators=[validators.InputRequired(), validators.Length(max=50)])
    clientPhone = StringField('Ваш телефон', validators=[validators.InputRequired(), validators.Length(max=12)])
    submit = SubmitField('Найдите мне преподавателя')


@app.route("/")
def render_index():
    random_teachers = db.session.query(Teacher).order_by(func.random()).limit(6)
    output = render_template('index.html', goals=goals, teachers=random_teachers)
    return output


@app.route("/all/")
def render_all():
    all_teachers = db.session.query(Teacher).order_by(Teacher.name).all()
    output = render_template('index.html', goals=goals, teachers=all_teachers)
    return output


@app.route("/goals/<goal>/")
def render_goal(goal):
    goal = db.session.query(Goal).filter(Goal.alias == goal).first()
    if goal is None:
        abort(404)
    output = render_template('goal.html', goal=goal)
    return output


@app.route("/profiles/<int:id>/")
def render_profile(id):
    teacher = db.session.query(Teacher).get_or_404(id)
    output = render_template('profile.html', teacher=teacher, teacher_free=json.loads(teacher.free), days=days)
    return output


@app.route("/request/", methods=['GET', 'POST'])
def render_request_form():
    form = RequestForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            selected_goal = db.session.query(Goal).filter(Goal.alias == form.goal.data).first()
            if selected_goal is None:
                abort(404)
            new_request = Request(
                goal_id = selected_goal.id,
                time = form.time.data,
                client_name = form.clientName.data,
                client_phone = form.clientPhone.data
            )
            db.session.add(new_request)
            db.session.commit()
            output = render_template('request_done.html', request=new_request)
        else:
            output = render_template('request.html', form=form)
    else:
        output = render_template('request.html', form=form)
    return output


@app.route("/booking/<int:id>/<day>/<time>/")
def render_booking_form(id, day, time):
    teacher = db.session.query(Teacher).get_or_404(id)
    if day not in days or len(time) > 5:
        abort(404)
    form = BookingForm()
    output = render_template('booking.html', day=day, time=time, days=days, teacher=teacher, form=form)
    return output


@app.route("/booking_done/", methods=['POST'])
def render_booking_done():
    form = BookingForm()
    teacher = db.session.query(Teacher).get_or_404(form.clientTeacher.data)
    weekday = db.session.query(Weekday).filter(Weekday.alias == form.clientWeekday.data).first()
    if weekday is None or len(form.clientTime.data) > 5:
        abort(404) # защита от подмены hidden полей (хакер не пройдёт!)

    if form.validate_on_submit():
        new_booking = Booking(
            teacher_id = teacher.id,
            weekday_id = weekday.id,
            time = form.clientTime.data,
            client_name = form.clientName.data,
            client_phone = form.clientPhone.data
        )
        db.session.add(new_booking)
        db.session.commit()
        output = render_template('booking_done.html', booking=new_booking)
    else:
        output = render_template('booking.html', day=form.clientWeekday.data, time=form.clientTime.data, days=days,
                                     teacher=teacher, form=form)
    return output


if __name__ == '__main__':
    app.run()