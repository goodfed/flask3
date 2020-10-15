import json
import random

from flask import Flask, render_template, abort, request
from flask_wtf import FlaskForm
import wtforms

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'

days = {
    "mon": "Понедельник",
    "tue": "Вторник",
    "wed": "Среда",
    "thu": "Четверг",
    "fri": "Пятница",
    "sat": "Суббота",
    "sun": "Воскресенье"
}

with open('goals.json', 'r') as g:
    goals = json.load(g)

goals_select = []
for value, title in goals.items():
    goals_select.append((value, title))

with open('teachers.json', 'r') as t:
    teachers = json.load(t)

def get_teacher(teachers, id):
    teacher = {}
    for t in teachers:
        if t['id'] == id:
            teacher = t
    return teacher

def get_teachers_by_goal(teachers, goal):
    choosed_teachers = []
    for t in teachers:
        if goal in t['goals']:
            choosed_teachers.append(t)
    return choosed_teachers

def get_random_teachers(teachers, count):
    return random.sample(teachers, k=count)

class BookingForm(FlaskForm):
    clientWeekday = wtforms.HiddenField('День недели', validators=[wtforms.validators.InputRequired()])
    clientTime = wtforms.HiddenField('Время', validators=[wtforms.validators.InputRequired()])
    clientTeacher = wtforms.HiddenField('Учитель', validators=[wtforms.validators.InputRequired()])
    clientName = wtforms.StringField('Вас зовут', validators=[wtforms.validators.InputRequired()])
    clientPhone = wtforms.StringField('Ваш телефон', validators=[wtforms.validators.InputRequired()])
    submit = wtforms.SubmitField('Записаться на пробный урок')

class RequestForm(FlaskForm):
    goal = wtforms.RadioField('Какая цель занятий?', choices=goals_select, default=goals_select[0][0])
    time = wtforms.RadioField('Сколько времени есть?', choices=[
        ('1-2', '1-2 часа в неделю'),
        ('3-5', '3-5 часов в неделю'),
        ('5-7', '5-7 часов в неделю'),
        ('7-10', '7-10 часов в неделю')
    ], default='1-2')
    clientName = wtforms.StringField('Вас зовут', validators=[wtforms.validators.InputRequired()])
    clientPhone = wtforms.StringField('Ваш телефон', validators=[wtforms.validators.InputRequired()])
    submit = wtforms.SubmitField('Найдите мне преподавателя')

@app.route("/")
def render_index():
    random_teachers = get_random_teachers(teachers, 6)
    output = render_template('index.html', goals=goals, teachers=random_teachers)
    return output

@app.route("/all/")
def render_all():
    output = render_template('all.html', goals=goals, teachers=teachers)
    return output

@app.route("/goals/<goal>/")
def render_goal(goal):
    if goal not in goals:
        abort(404)

    print(goal)
    teachers_by_goal = get_teachers_by_goal(teachers, goal)
    print(teachers_by_goal)
    output = render_template('goal.html', goals=goals, goal=goal, teachers=teachers_by_goal)
    return output


@app.route("/profiles/<int:id>/")
def render_profile(id):
    teacher = get_teacher(teachers, id)
    if not teacher:
        abort(404)

    output = render_template('profile.html', days=days, teacher=teacher, goals=goals)
    return output


@app.route("/request/", methods=['GET', 'POST'])
def render_request_form():
    form = RequestForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            with open('request.json', 'r') as r:
                req = json.load(r)
            with open('request.json', 'w') as r:
                req.append({
                    'goal': form.goal.data,
                    'time': form.time.data,
                    'clientName': form.clientName.data,
                    'clientPhone': form.clientPhone.data
                })
                json.dump(req, r)

            output = render_template('request_done.html', goals=goals, form=form)
        else:
            output = render_template('request.html', form=form)
    else:
        output = render_template('request.html', form=form)
    return output


@app.route("/booking/<int:id>/<day>/<time>/")
def render_booking_form(id, day, time):
    teacher = get_teacher(teachers, id)
    if not teacher or day not in days:
        abort(404)

    form = BookingForm()
    output = render_template('booking.html', day=day, time=time, days=days, teacher=teacher, form=form)
    return output


@app.route("/booking_done/", methods=['POST'])
def render_booking_done():
    form = BookingForm()
    clientTeacher = form.clientTeacher.data
    clientWeekday = form.clientWeekday.data
    clientTime = form.clientTime.data
    clientName = form.clientName.data
    clientPhone = form.clientPhone.data

    if form.validate_on_submit():
        with open('booking.json', 'r') as b:
            bookings = json.load(b)
        with open('booking.json', 'w') as b:
            bookings.append({
                'clientTeacher': clientTeacher,
                'clientWeekday': clientWeekday,
                'clientTime': clientTime,
                'clientName': clientName,
                'clientPhone': clientPhone,
            })
            json.dump(bookings, b)

        output = render_template('booking_done.html', days=days, clientTime=clientTime, clientWeekday=clientWeekday,
                                 clientName=clientName, clientPhone=clientPhone)
    else:
        teacher = get_teacher(teachers, int(clientTeacher))
        if not teacher or clientWeekday not in days or not clientTime:
            abort(404) # что-то подменили в скрытых полях, хакеры :)
        else:
            output = render_template('booking.html', day=clientWeekday, time=clientTime, days=days,
                                     teacher=teacher, form=form)

    return output


if __name__ == '__main__':
    app.run()