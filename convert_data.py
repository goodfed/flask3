import json

import data

with open('data/goals.json', 'w') as g:
    json.dump(data.goals, g)

with open('data/teachers.json', 'w') as t:
    json.dump(data.teachers, t)