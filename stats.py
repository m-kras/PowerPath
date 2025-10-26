import ast


def get_avg_reps(workout_list):
    if len(workout_list) > 0:
        reps = []

        for workout in workout_list:
            for key, value in workout.items():
                if key not in ["Date", "Comment"] and value != "":
                    value = ast.literal_eval(value)  # convert to literal list object
                    for obj in value:  # for every set of an exercise
                        reps.append(obj[1].replace(" Reps", ""))  # add rep number to list

        # calculate average
        rep_sum = 0
        for nr in reps:
            rep_sum += int(nr)

        avg_reps = rep_sum / len(reps)  # sum of reps / number of sets

        return str(avg_reps)

    else:
        return "N/A"


def get_fav_exercise(workout_list, exercises):
    if len(workout_list) > 0:
        counting_dict = {}

        for exercise in exercises:
            counting_dict.update({exercise: 0})  # prepare the dict inside of counting_list

        for workout in workout_list:
            for key, value in workout.items():
                if key not in ["Date", "Comment"] and value != "":
                    value = ast.literal_eval(value)  # convert to literal list object
                    for _ in value:  # for every set of an exercise
                        counting_dict.update({key: counting_dict[key] + 1})  # add +1 to the exercise

        highest = 0
        fav_ex = ""
        for key, value in counting_dict.items():
            if value > highest:  # comparing sets numbers
                highest = value
                fav_ex = key

        return fav_ex

    else:
        return "N/A"



