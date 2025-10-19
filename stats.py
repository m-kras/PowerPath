import re

def get_avg_rep_nr(workout_list):
    print(str(workout_list))
    matches = re.search(r"(\d+) Reps", str(workout_list))
    print(matches)