import json

import data

with open('static/goals.json', 'w') as g:
    json.dump(data.goals, g)

with open('static/teachers.json', 'w') as t:
    json.dump(data.teachers, t)