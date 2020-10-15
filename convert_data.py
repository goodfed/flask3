import json

import data

with open('goals.json', 'w') as g:
    json.dump(data.goals, g)

with open('teachers.json', 'w') as t:
    json.dump(data.teachers, t)