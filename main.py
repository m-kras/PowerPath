# kivy imports
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition
from kivy.uix.popup import Popup
from kivy.core.window import Window

# other imports
import csv
import os.path
from datetime import date
from datetime import datetime
from pathlib import Path
import ast
from tabulate import tabulate

__version__ = '1.2.9'


class HomeScreen(Screen):
    pass


class HowToScreen(Screen):
    pass


class ManageScreen(Screen):
    pass


class AddPlanScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_pre_enter(self, *args):
        # reset widgets etc.
        self.added_exercises = []
        self.ids.exercise_input.hint_text = "Exercise 1"
        self.ids.exercise_input.text = ""
        self.ids.name_input.text = ""
        self.ids.feedback_label.text = ""

    def add_exercise(self):
        exercise = self.ids.exercise_input.text.strip() # get exercise input

        # valid input
        if (exercise.replace("(", "").replace(")", "").replace("-", "")
                    .replace(" ", "").replace(".", "")
                    .isalnum() is True) and (exercise not in self.added_exercises):
            self.added_exercises.append(exercise)

            # configure positive feedback
            self.ids.feedback_label.text = "Exercise added!"
            self.ids.feedback_label.color = 0, 1, 0, 1
            self.ids.feedback_label.bold = True

            # update exercise_input's hint_text
            exercise_nr = int(self.ids.exercise_input.hint_text[-1]) # nr = last character of hint_text
            self.ids.exercise_input.hint_text = f"Exercise {exercise_nr + 1}" # new hint_text (e.g. Exercise 1 -> 2)
            self.ids.exercise_input.text = ""

        # empty input
        elif exercise == "":
            # configure negative feedback
            self.ids.feedback_label.text = "Please pass in an exercise."
            self.ids.feedback_label.color = 1, 0, 0, 1
            self.ids.feedback_label.bold = True

            self.ids.exercise_input.text = ""

        # exercise already added
        elif exercise in self.added_exercises:
            # configure negative feedback
            self.ids.feedback_label.text = "Exercise has already been added."
            self.ids.feedback_label.color = 1, 0, 0, 1
            self.ids.feedback_label.bold = True

            self.ids.exercise_input.text = ""  # clear text

        # incorrect syntax
        else:
            # configure negative feedback
            self.ids.feedback_label.text = "Allowed characters: a-z, 0-9, (), -, ., Space"
            self.ids.feedback_label.color = 1, 0, 0, 1
            self.ids.feedback_label.bold = True

            self.ids.exercise_input.text = ""

    # save the workout
    def save_plan(self):
        name = self.ids.name_input.text # get workout plan name

        # creation of {plan's name}.csv
        if len(self.added_exercises) > 0: # exercises must have been added
            if name != "": # must have a name
                if os.path.isfile(self.app.get_data_path(f"{name.strip()}.csv")) is False: # check whether plan already exists

                    self.added_exercises.insert(0, "Date") # header: Date, Ex1, Ex2, ...
                    self.added_exercises.append("Comment") # last key should be comment

                    # create workout (plan)-specific csv file
                    with open(self.app.get_data_path(f"{name}.csv"), "w", newline="") as file:
                        writer = csv.DictWriter(file, fieldnames=self.added_exercises, delimiter=";")
                        writer.writeheader() # write header (Date, Ex1, Ex2, ..., Comment)

                    # adding name to all_workouts.csv
                    with open(self.app.get_data_path("all_workouts.csv"), "a", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow([name])

                    # return to home screen
                    self.manager.transition.direction = "right"
                    self.manager.current = "home"

                # workout name already used
                else:
                    # configure negative feedback
                    self.ids.feedback_label.text = "Workout name already used."
                    self.ids.feedback_label.color = 1, 0, 0, 1
                    self.ids.feedback_label.bold = True

            # workout not named
            else:
                # configure negative feedback
                self.ids.feedback_label.text = "Please add a name."
                self.ids.feedback_label.color = 1, 0, 0, 1
                self.ids.feedback_label.bold = True

        # exercise list empty
        else:
            # configure negative feedback
            self.ids.feedback_label.text = "No Exercises added."
            self.ids.feedback_label.color = 1, 0, 0, 1
            self.ids.feedback_label.bold = True

    # cancel button pressed
    def open_popup(self):
        if self.added_exercises != []: # open popup only if exercises added
            popup = CancelPopup()
            popup.open()

        else: # no exercises added => no popup necessary
            self.manager.transition.direction = "right"
            self.manager.current = "manage"


class DelPlanScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_pre_enter(self):
        self.plan_list = self.app.get_workouts()  # list with all the currently saved workouts

        self.ids.delplan_spinner.values = self.plan_list  # update spinner values on every re-entry
        self.ids.delplan_spinner.text = "Select Plan"

    # open popup if deletion button pressed
    def open_popup(self):
        if self.ids.delplan_spinner.text != "Select Plan": # must be selected
            popup = DelPlanPopup()
            popup.plan_list = self.plan_list # pass on plan_list
            popup.plan = self.ids.delplan_spinner.text  # pass on the chosen exercise
            popup.open()

        else: # if no plan selected
            self.ids.feedback_label.text = "No plan selected."
            self.ids.feedback_label.color = 1, 0, 0, 1


class StartSessionScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_pre_enter(self, *args):
        # labels/texts etc.
        self.ids.workout_spinner.text = "Select Workout"
        self.ids.feedback_label.text = ""

        # update spinner values
        workout_list = self.app.get_workouts()  # list with all the currently saved workouts
        self.ids.workout_spinner.values = workout_list

        # set date (user is able to overwrite it)
        today = date.today().strftime("%d/%m/%Y") # current date (dd-mm-yyyy)
        self.ids.date_input.text = today # set text of date_input to current date

    def start_session(self):
        if self.ids.workout_spinner.text != "Select Workout": # workout must be selected
            # check whether date has been used already
            with open(self.app.get_data_path(f"{self.ids.workout_spinner.text}.csv"), "r",
                      newline="") as file:
                dictreader = csv.DictReader(file, delimiter=";")
                for workout in dictreader:
                    if workout["Date"] == self.ids.date_input.text:
                        self.ids.feedback_label.text = "Date has been used already."
                        self.ids.feedback_label.color = 1, 0, 0, 1
                        return

            # check for correct date format
            date_check = False
            try:
                datetime.strptime(self.ids.date_input.text, "%d/%m/%Y")
                if len(self.ids.date_input.text) == 10:
                    date_check = True
            except ValueError as e:
                print(e)
                pass

            if date_check: # run only if date format is valid
                self.app.custom_var = [self.ids.workout_spinner.text, self.ids.date_input.text]  # share workout, date

                self.manager.transition.direction = "left"
                self.manager.current = "session" # switch to SessionScreen

            else: # date_check is False
                self.ids.feedback_label.text = "Date invalid."
                self.ids.feedback_label.color = 1, 0, 0, 1

        else: # no workout selected
            # configure negative feedback
            self.ids.feedback_label.text = "Please select a workout."
            self.ids.feedback_label.color = 1, 0, 0, 1


class SessionScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_pre_enter(self, *args):

        # get data through app's custom_var
        if type(self.app.custom_var[1]) != dict:
            self.current_workout = self.app.custom_var[0]
            self.current_date = self.app.custom_var[1]
        else:
            self.current_workout = self.app.custom_var[0]
            self.current_date = self.app.custom_var[1]["Date"]

        # get exercises/previous workouts
        self.exer_list = [] # list to store exercises (from csv header)
        self.prev_workouts = [] # list of dicts (!) to store the previous workouts

        with open(self.app.get_data_path(f"{self.current_workout}.csv"), "r") as file:
            dictreader = csv.DictReader(file, delimiter=";")

            for obj in dictreader.fieldnames: # for every header object
                self.exer_list.append(obj) # append the headers of the file (date + exercises) to list

            # remove date and comment (only exercises required)
            self.exer_list.remove("Date")
            self.exer_list.remove("Comment")
            self.current_exercise = self.exer_list[0]

            for obj in dictreader:
                self.prev_workouts.append(obj) # append everything to prev_workouts (list of dicts)

        # set labels etc.
        self.ids.exerset_label.text = f"{self.current_exercise} - Set 1" # show first exercise and Set 1
        self.ids.date_label.text = self.current_date # set date label
        # reset widgets
        self.ids.weight_input.text = ""
        self.ids.reps_input.text = ""
        self.ids.weight_input.hint_text = "Weight in KG"
        self.ids.reps_input.hint_text = "Reps"
        self.ids.feedback_label.text = ""
        self.ids.comment_input.text = ""
        self.ids.comment_input.hint_text = "Comment"
        self.ids.prev_btn.opacity = 1
        self.ids.prev_btn.disabled = False

        # for editing mode
        if type(self.app.custom_var[1]) == dict:
            self.ids.weight_input.text = ast.literal_eval(self.app.custom_var[1][self.current_exercise])[0][0].replace(" KG", "")
            self.ids.reps_input.text = ast.literal_eval(self.app.custom_var[1][self.current_exercise])[0][1]. replace(" Reps", "")
            self.ids.comment_input.text = self.app.custom_var[1]["Comment"]
            # hide prev_btn in editing mode
            self.ids.prev_btn.opacity = 0
            self.ids.prev_btn.disabled = True

        # list and dict (storing data throughout the session)
        self.workout_dict = {"Date": self.current_date} # dict for the entire workout (to write into csv)
        self.current_exercise_sets = [] # list containing all the sets ([weight, reps]) for a given exercise

    def get_prev_workout(self):

        # find most recent workout date
        if self.prev_workouts != []: # if there are any previous workouts
            recent_date = datetime.strptime(self.prev_workouts[0]["Date"], "%d/%m/%Y").date()

            for obj in self.prev_workouts[1:]:  # for dict in prev_workouts (skipping first object [see above])
                if datetime.strptime(obj["Date"],
                                     "%d/%m/%Y").date() > recent_date:  # if date of this workout comes after date of the workout before
                    recent_date = datetime.strptime(obj["Date"], "%d/%m/%Y").date()

        else:
            return "No previous Workouts..."

        for obj in self.prev_workouts:  # loop again to find workout with fitting date
            if datetime.strptime(obj["Date"], "%d/%m/%Y").date() == recent_date:  # if date found
                prev_workout = obj  # assign correct dict (prev workout) to variable
                break

        workout_str = f"Previous: {prev_workout['Date']}\n\n" # start of workout_str

        data_list = [["Exercise", "Weight", "Reps"]] # header

        for key, value in list(prev_workout.items())[
                          1:-1]:  # iterating over a list of tuples, each containing a key and value
            if value != "":

                value = ast.literal_eval(value)  # convert str rep. of list into actual list

                for obj in value:  # for every set of an exercise
                    data_list.append([key, obj[0], obj[1]]) # append data, weight, set

        workout_str += tabulate(data_list, headers="firstrow", tablefmt="fancy_grid")

        if prev_workout["Comment"] != "": # if the user wrote a comment for this workout
            workout_str += f"\nComment: {prev_workout['Comment']}" # add comment to the string

        return workout_str

    def add_set(self):
        # get input values
        weight = self.ids.weight_input.text.strip()
        reps = self.ids.reps_input.text.strip()

        # checks
        if weight.replace(".", "").replace(",", "").isnumeric() and reps.isnumeric(): # input must be numeric (except "." and ",")
            self.current_exercise_sets.append([f"{weight} KG", f"{reps} Reps"]) # append both values to list (in form of a list)

            # configure pos. feedback
            self.ids.feedback_label.text = "Set added!"
            self.ids.feedback_label.color = 0, 1, 0, 1

            # update set number
            set_nr = int(self.ids.exerset_label.text[-1])  # nr = last character (assumption: <9 sets per exercise)
            self.ids.exerset_label.text = f"{self.current_exercise} - Set {set_nr + 1}"

            # configure inputs
            self.ids.weight_input.text = ""
            self.ids.reps_input.text = ""

            if type(self.app.custom_var[1]) == dict:
                try: # try to get the original values of the next set
                    self.ids.weight_input.text = ast.literal_eval(self.app.custom_var[1][self.current_exercise])[set_nr][0].replace(" KG", "")
                    self.ids.reps_input.text = ast.literal_eval(self.app.custom_var[1][self.current_exercise])[set_nr][1].replace(" Reps", "")

                except (IndexError, SyntaxError) as e: # no more sets of this exercise available
                    print(e)
                    pass

        else:
            # configure neg. feedback
            self.ids.feedback_label.text = "Invalid input."
            self.ids.feedback_label.color = 1, 0, 0, 1

    def next_exercise(self):
        new_index = self.exer_list.index(self.current_exercise) + 1  # old index in exer_list + 1

        if new_index <= len(self.exer_list) - 1: # last exercise
            self.sets_to_dict() # write current sets into dict

            self.current_exercise = self.exer_list[new_index]  # get new exercise
            self.ids.exerset_label.text = f"{self.current_exercise} - Set 1" # new exerset_label text

            # update labels, input boxes
            self.ids.weight_input.text = ""
            self.ids.reps_input.text = ""
            self.ids.feedback_label.text = ""

            if type(self.app.custom_var[1]) == dict:
                try: # try to show values of first set of next exercise
                    self.ids.weight_input.text = ast.literal_eval(self.app.custom_var[1][self.current_exercise])[0][0].replace(" KG", "")
                    self.ids.reps_input.text = ast.literal_eval(self.app.custom_var[1][self.current_exercise])[0][1].replace(" Reps", "")

                except (IndexError, SyntaxError) as e:
                    print(e)
                    pass

        else: # last exercise already reached
            self.ids.feedback_label.text = "This is the final exercise."
            self.ids.feedback_label.color = 1, 0, 0, 1

    # write sets into dict
    def sets_to_dict(self):
        # add exercise sets to workout dict
        if len(self.current_exercise_sets) > 0: # if sets given
            self.workout_dict.update(
                {self.current_exercise: self.current_exercise_sets})  # {exer_name: [[w1, r1],[w2,r2],...]}
            self.current_exercise_sets = [] # reset list with current sets

    def save_session(self):
        prev_workouts = []

        self.sets_to_dict() # write last sets into dict
        self.workout_dict.update({"Comment": self.ids.comment_input.text.strip()}) # add comment to dict

        if self.workout_dict != {"Date": self.current_date, "Comment": self.ids.comment_input.text.strip()}: # sets must have been added
            with open(self.app.get_data_path(f"{self.current_workout}.csv"), "r", newline="") as file: # open in read mode
                dictreader = csv.DictReader(file, delimiter=";")
                fieldnames = dictreader.fieldnames # get fieldnames of csv
                for workout in dictreader:
                    if workout["Date"] != self.current_date: # ignore original workout with this date
                        prev_workouts.append(workout)

            prev_workouts.append(self.workout_dict)

            sorted_workouts = sorted(prev_workouts, key=lambda x: datetime.strptime(x["Date"], "%d/%m/%Y"), reverse=True)

            with open(self.app.get_data_path(f"{self.current_workout}.csv"), "w", newline="") as file:
                dictwriter = csv.DictWriter(file, delimiter=";", fieldnames=fieldnames)
                dictwriter.writeheader()
                for workout in sorted_workouts:
                    dictwriter.writerow(workout)

            self.app.custom_var = ""

            # switch to home screen
            self.manager.transition.direction = "right"
            self.manager.current = "home"

        # if no sets added
        else:
            self.ids.feedback_label.text = "No sets added."
            self.ids.feedback_label.color = 1, 0, 0, 1

    # open popup to show the previous workout
    def open_prev_popup(self):
        popup = PrevPopup()
        popup.ids.prev_label.text = self.get_prev_workout() # pass on the prev. workout string
        popup.open()


class PastScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_pre_enter(self, *args):
        # update spinners
        workout_list = self.app.get_workouts()  # list with all the currently saved workouts
        self.ids.workout_spinner.values = workout_list  # update spinner values on every re-entry
        self.ids.workout_spinner.text = "Select Workout"
        self.ids.date_spinner.text = "Select Date"

        # configure widgets (hide/show/clear text)
        self.edit_or_show(True) # showing mode by default
        self.ids.main_rv.data = ""
        self.ids.feedback_label.text = ""
    def get_str_list(self, workout_name):
        dict_list = []
        result = []

        with open(self.app.get_data_path(f"{workout_name}.csv"), "r") as file:
            dictreader = csv.DictReader(file, delimiter=";")

            for obj in dictreader:  # for each dictionary (a dict is a workout)
                dict_list.append(obj)

        sorted_list = sorted(dict_list, key=lambda x: datetime.strptime(x["Date"], "%d/%m/%Y"), reverse=True)

        for obj in sorted_list: # for each dictionary (a dict is a workout)
            entry_str = f"Date: {obj['Date']}\n\n"  # add date of workout
            comment = ""
            data_list = [["Exercise", "Weight", "Reps"]] # header row

            for key, value in list(obj.items())[1:]:  # iterating over a list of tuples, each containing a key and value
                if value != "" and key != "Comment":

                    value = ast.literal_eval(value)  # convert str rep. of list into actual list

                    for i in value:  # for every set of an exercise
                        data_list.append([key, i[0], i[1]]) # append new row for this set

                elif key == "Comment" and value != "": # if the user wrote a comment for this workout
                    comment = f"Comment: {obj['Comment']}"

            workout_table = tabulate(data_list, headers="firstrow", tablefmt="fancy_grid")

            if comment != "":
                entry_str += f"{workout_table}\n{comment}\n\n\n" # create a string with a date, table and comment

            else:
                entry_str += f"{workout_table}\n\n\n" # without comment

            result.append(entry_str)

        return result

    def show_past_workouts(self):
        self.ids.feedback_label.text = ""  # clear feedback_label if button pressed
        self.edit_or_show(True)  # configure widgets (showing mode)

        if self.ids.workout_spinner.text != "Select Workout":  # workout must be selected
            self.ids.main_rv.data = [{"text": workout_str} for workout_str
                                     in self.get_str_list(self.ids.workout_spinner.text)] # update recycleview

        else: # no workout selected
            self.ids.feedback_label.text = "Please select a Workout."
            self.ids.feedback_label.color = 1, 0, 0, 1

    def switch_to_editor(self):
        to_share = [self.ids.workout_spinner.text]

        if self.ids.date_spinner.text != "Select Date":
            with open(self.app.get_data_path(f"{self.ids.workout_spinner.text}.csv"), "r") as file:
                dictreader = csv.DictReader(file, delimiter=";")
                for workout in dictreader:
                    if workout["Date"] == self.ids.date_spinner.text: # find equivalent workout from csv
                        to_share.append(workout)
                        self.app.custom_var = to_share # share workout name and dict through custom_var
                        break

            self.manager.transition.direction = "left"
            self.manager.current = "session"

        else:
            self.ids.feedback_label.text = "Please select a workout date."
            self.ids.feedback_label.color = 1, 0, 0, 1

    def open_delwrk_popup(self):
        if self.ids.date_spinner.text != "Select Date":
            popup = DelWrkPopup()
            popup.workout_name = self.ids.workout_spinner.text
            popup.workout_date = self.ids.date_spinner.text
            popup.open()

        else:
            self.ids.feedback_label.text = "Please select a workout date."
            self.ids.feedback_label.color = 1, 0, 0, 1

    def edit_or_show(self, showing_mode):
        if showing_mode: # True as parameter -> showing mode

            self.ids.main_rv.opacity = 1
            self.ids.main_rv.disabled = False
            self.ids.main_rv.size_hint_y = 0.5
            self.ids.main_rv.height = self.height * 0.5

            for wid in [self.ids.date_spinner, self.ids.edit_btn, self.ids.del_btn]:
                wid.opacity = 0
                wid.disabled = True
                wid.height = 0
                wid.size_hint_y = None

        else: # False as parameter -> editing mode
            self.ids.main_rv.opacity = 0
            self.ids.main_rv.disabled = True
            self.ids.main_rv.size_hint_y = None
            self.ids.main_rv.height = 0

            self.ids.date_spinner.opacity = 1
            self.ids.date_spinner.disabled = False
            self.ids.date_spinner.height = self.height * 0.07
            self.ids.date_spinner.size_hint_y = None

            self.ids.edit_btn.opacity = 1
            self.ids.edit_btn.disabled = False
            self.ids.edit_btn.height = self.height * 0.1
            self.ids.edit_btn.size_hint_y = None

            self.ids.del_btn.opacity = 1
            self.ids.del_btn.disabled = False
            self.ids.del_btn.height = self.height * 0.1
            self.ids.del_btn.size_hint_y = None

            all_dates = []
            with open(self.app.get_data_path(f"{self.ids.workout_spinner.text}.csv"), "r") as file:
                dictreader = csv.DictReader(file, delimiter=";")
                for workout in dictreader:
                    all_dates.append(workout["Date"]) # get all dates

            sorted_dates = sorted(all_dates, key=lambda x: datetime.strptime(x, "%d/%m/%Y"), reverse=True)
            self.ids.date_spinner.values = sorted_dates

class DelWrkPopup(Popup):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
    def on_pre_open(self):
        self.ids.wrk_date_label.text = f"{self.workout_name} from {self.workout_date}"

    def del_workout(self):
        dict_list = []

        with open(self.app.get_data_path(f"{self.workout_name}.csv"), "r") as file:
            dictreader = csv.DictReader(file, delimiter=";")
            fieldnames = dictreader.fieldnames

            for workout in dictreader:
                if workout["Date"] != self.workout_date: # append every workout except for the one to be deleted
                    dict_list.append(workout)

        sorted_list = sorted(dict_list, key=lambda x: datetime.strptime(x["Date"], "%d/%m/%Y"), reverse=True)

        with open(self.app.get_data_path(f"{self.workout_name}.csv"), "w", newline="") as file:
            dictwriter = csv.DictWriter(file, delimiter=";", fieldnames=fieldnames)
            dictwriter.writeheader()

            for workout in sorted_list:
                dictwriter.writerow(workout)


class DelPlanPopup(Popup):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    # deleting the selected workout plan
    def del_plan(self):
        os.remove(self.app.get_data_path(f"{self.plan}.csv")) # delete workout(plan)-specific file

        self.plan_list.remove(self.plan) # remove plan's name from plan_list
        with open(self.app.get_data_path("all_workouts.csv"), "w", newline="") as file: # open in writing mode to overwrite
            writer = csv.writer(file)
            writer.writerow(["Workouts"]) # write header
            for obj in self.plan_list:
                writer.writerow([obj]) # add every remaining workout plan


class PrevPopup(Popup):
    pass


class CancelPopup(Popup):
    pass


class WarningPopup(Popup):
    pass


class MyScreenManager(ScreenManager):
    pass


# App class
class Powerpath(App):
    custom_var = "" # variable that all screens can access to share data

    def build(self):
        Window.bind(on_keyboard=self.check_pressed_button)

        # initializing screen manager that contains all windows
        sm = MyScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(HowToScreen(name="howto"))
        sm.add_widget(PastScreen(name="past"))
        sm.add_widget(ManageScreen(name="manage"))
        sm.add_widget(AddPlanScreen(name="addplan"))
        sm.add_widget(DelPlanScreen(name="delplan"))
        sm.add_widget(StartSessionScreen(name="startsession"))
        sm.add_widget(SessionScreen(name="session"))

        # create .csv to save all the workouts (upon first app launch)
        if not self.get_data_path("all_workouts.csv").is_file():
            with open(self.get_data_path("all_workouts.csv"), "a", newline="") as file: # creation of all_workouts.csv
                writer = csv.writer(file)
                writer.writerow(["Workouts"]) # write header

        return sm # start the app (screenmanager as the main widget)

    # return path where a file should be stored (for csv's)
    def get_data_path(self, filename):
        data_dir = Path(self.user_data_dir) # create Path object (dir in app's internal storage)
        data_dir.mkdir(parents=True, exist_ok=True) # check if directory exists, if not then create it

        return data_dir / filename # combine safe directory with file name

    def check_pressed_button(self, window, key, *args):
        if key == 27: # 27 == android back button
            self.open_warning()
            return True # prevent closing of the app (default behaviour)
        else: # other button pressed
            return False

    def open_warning(self):
        popup = WarningPopup()
        popup.open()

    # return a list with all the currently saved workout plans
    def get_workouts(self):

        self.workout_list = []

        with open(self.get_data_path("all_workouts.csv"), "r") as file:
            reader = csv.reader(file)
            next(reader)  # skip header ("Workouts")
            for line in reader:
                for obj in line:  # iterating over each of the lists to get individual strings
                    self.workout_list.append(obj)  # append all available exercises to list

        return self.workout_list


if __name__ == "__main__":
    Powerpath().run()
