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
import re


__version__ = '1.2.1'


class HomeScreen(Screen):
    pass


class HowToScreen(Screen):
    pass


class ManageScreen(Screen):
    pass


class AddWrkScreen(Screen):

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
    def save_workout(self):
        app = App.get_running_app() # for get_data_path

        name = self.ids.name_input.text # get workout name

        # creation of {workout name}.csv
        if len(self.added_exercises) > 0: # exercises must have been added
            if name != "": # workout must have a name
                if os.path.isfile(app.get_data_path(f"{name.strip()}.csv")) is False: # check whether workout already exists

                    self.added_exercises.insert(0, "Date") # header: Date, Ex1, Ex2, ...
                    self.added_exercises.append("Comment") # last key should be comment

                    # create workout-specific csv file
                    with open(app.get_data_path(f"{name}.csv"), "w", newline="") as file:
                        writer = csv.DictWriter(file, fieldnames=self.added_exercises, delimiter=";")
                        writer.writeheader() # write header (Date, Ex1, Ex2, ..., Comment)

                    # adding name to all_workouts.csv
                    with open(app.get_data_path("all_workouts.csv"), "a", newline="") as file:
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


class DelWrkScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        self.workout_list = app.get_workouts()  # list with all the currently saved workouts

        self.ids.delwrk_spinner.values = self.workout_list  # update spinner values on every re-entry
        self.ids.delwrk_spinner.text = "Select Workout"

    # open popup if deletion button pressed
    def open_popup(self):
        if self.ids.delwrk_spinner.text != "Select Workout": # must be selected
            popup = DelWrkPopup()
            popup.workout_list = self.workout_list # pass on workout_list
            popup.workout = self.ids.delwrk_spinner.text  # pass on the chosen exercise
            popup.open()

        else: # if no workout selected
            self.ids.feedback_label.text = "No workout selected."
            self.ids.feedback_label.color = 1, 0, 0, 1



class StartSessionScreen(Screen):
    def on_pre_enter(self, *args):
        # labels/texts etc.
        self.ids.workout_spinner.text = "Select Workout"
        self.ids.feedback_label.text = ""

        # update spinner values
        app = App.get_running_app()
        workout_list = app.get_workouts()  # list with all the currently saved workouts
        self.ids.workout_spinner.values = workout_list

        # set date (user is able to overwrite it)
        today = date.today().strftime("%d/%m/%Y") # current date (dd-mm-yyyy)
        self.ids.date_input.text = today # set text of date_input to current date

    def start_session(self):
        if self.ids.workout_spinner.text != "Select Workout": # workout must be selected

            date_check = True
            try:
                datetime.strptime(self.ids.date_input.text, "%d/%m/%Y") # check if date correct
            except ValueError:
                pass
                date_check = False

            if date_check: # run only if date format is valid

                App.get_running_app().custom_var = [self.ids.workout_spinner.text, self.ids.date_input.text]  # share workout, date

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
    def on_pre_enter(self, *args):
        app = App.get_running_app()  # for get_data_path

        # get data from prev. screen
        self.current_workout = App.get_running_app().custom_var[0]
        self.current_date = App.get_running_app().custom_var[1]

        # get exercises/previous workouts
        self.exer_list = [] # list to store exercises (from csv header)
        self.prev_workouts = [] # list of dicts (!) to store the previous workouts

        with open(app.get_data_path(f"{self.current_workout}.csv"), "r") as file:
            dictreader = csv.DictReader(file, delimiter=";")

            for obj in dictreader.fieldnames: # for every header object
                self.exer_list.append(obj) # append the headers of the file (date + exercises) to list

            self.exer_list.remove("Date") # remove date (only exercises needed for now)
            self.current_exercise = self.exer_list[0]

            for obj in dictreader:
                self.prev_workouts.append(obj) # append everything to prev_workouts (list of dicts)

        # set labels etc.
        self.ids.exerset_label.text = f"{self.current_exercise} - Set 1" # show first exercise and Set 1
        self.ids.date_label.text = self.current_date # set date label
        # reset widgets
        self.ids.weight_input.text = ""
        self.ids.reps_input.text = ""
        self.ids.feedback_label.text = ""
        self.ids.comment_input.text = ""

        # list and dict (storing data throughout the session)
        self.workout_dict = {"Date": self.current_date} # dict for the entire workout (to write into csv)
        self.current_exercise_sets = [] # list containing all the sets ([weight, reps]) for a given exercise

    def get_prev_workout(self):
        # find most recent workout date
        if self.prev_workouts != []:  # if there are any previous workouts
            recent_date = datetime.strptime(self.prev_workouts[0]["Date"], "%d/%m/%Y").date()  # convert to date obj.

            for obj in self.prev_workouts[1:]:  # for dict in prev_workouts (skipping first object [see above])
                if datetime.strptime(obj["Date"],
                                     "%d/%m/%Y").date() > recent_date:  # if date of this workout comes after date of the workout before
                    recent_date = datetime.strptime(obj["Date"], "%d/%m/%Y").date()

            # create a string to show the previous workout
            for obj in self.prev_workouts:  # loop again to find workout with fitting date
                if datetime.strptime(obj["Date"], "%d/%m/%Y").date() == recent_date:  # if date found
                    prev_workout = obj  # assign correct dict (prev workout) to variable
                    break

            workout_str = f"Previous: {prev_workout['Date']}\n"  # start of workout_str

            for key, value in list(prev_workout.items())[
                              1:-1]:  # iterating over a list of tuples, each containing a key and value
                if value != "":
                    workout_str = f"{workout_str}{key}: "  # first part of addition

                    value = ast.literal_eval(value)  # convert str rep. of list into actual list

                    for obj in value:  # for every set of an exercise
                        workout_str = f"{workout_str}\n({obj[0]}, {obj[1]})"  # second part of addition

                    workout_str = f"{workout_str}\n"  # add new line before next exercise

            if prev_workout["Comment"] != "": # if the user wrote a comment for this workout
                workout_str = f"{workout_str}Comment: {prev_workout['Comment']}" # add comment to the string

            return workout_str

        else:
            return "No previous Workouts..."

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
            self.ids.weight_input.text = ""
            self.ids.reps_input.text = ""

            # update set number
            set_nr = int(self.ids.exerset_label.text[-1])  # nr = last character (assumption: <9 sets per exercise)
            self.ids.exerset_label.text = f"{self.current_exercise} - Set {set_nr + 1}"

        else:
            # configure neg. feedback
            self.ids.feedback_label.text = "Invalid input."
            self.ids.feedback_label.color = 1, 0, 0, 1

    def next_exercise(self):
        new_index = self.exer_list.index(self.current_exercise) + 1  # old index in exer_list + 1

        if new_index <= len(self.exer_list) - 2: # last exercise (NOT comment) is len(list) - 2
            self.sets_to_dict() # write current sets into dict

            self.current_exercise = self.exer_list[new_index]  # get new exercise
            self.ids.exerset_label.text = f"{self.current_exercise} - Set 1" # new exerset_label text

            # update labels, input boxes
            self.ids.weight_input.text = ""
            self.ids.reps_input.text = ""
            self.ids.feedback_label.text = ""

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
        app = App.get_running_app()  # for get_data_path

        self.sets_to_dict() # write last sets into dict
        self.workout_dict.update({"Comment": self.ids.comment_input.text.strip()}) # add comment to dict

        if self.workout_dict != {"Date": self.current_date}: # sets must have been added
            with open(app.get_data_path(f"{self.current_workout}.csv"), "r", newline="") as file: # open in read mode
                dictreader = csv.DictReader(file, delimiter=";")
                fieldnames = dictreader.fieldnames # get fieldnames of csv

            with open(app.get_data_path(f"{self.current_workout}.csv"), "a", newline="") as file: # open in append mode
                dictwriter = csv.DictWriter(file, delimiter=";", fieldnames=fieldnames)
                dictwriter.writerow(self.workout_dict) # write values of dict into csv file

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
    def on_pre_enter(self, *args):
        # update spinners
        app = App.get_running_app()
        workout_list = app.get_workouts()  # list with all the currently saved workouts
        self.ids.workout_spinner.values = workout_list  # update spinner values on every re-entry
        self.ids.workout_spinner.text = "Select Workout"
        self.ids.date_spinner.text = "Select Date"

        # configure widgets (hide/show/clear text)
        self.edit_or_show(True) # showing mode by default
        self.ids.main_label.text = ""
        self.ids.feedback_label.text = ""
        self.ids.edit_box.text = ""
        self.ids.edit_feedback.text = ""

    def get_workouts_str(self, workout_name):
        app = App.get_running_app()  # for get_data_path
        dict_list = []

        with open(app.get_data_path(f"{workout_name}.csv"), "r") as file:
            dictreader = csv.DictReader(file, delimiter=";")

            for obj in dictreader:  # for each dictionary (a dict is a workout)
                dict_list.append(obj)

        sorted_list = sorted(dict_list, key=lambda x: datetime.strptime(x["Date"], "%d/%m/%Y"), reverse=True)

        workout_history = "" # string for entire workout history

        for obj in sorted_list: # for each dictionary (a dict is a workout)

            workout_history = f"{workout_history}\n\nDate: {obj['Date']}\n\n"  # add date of workout

            for key, value in list(obj.items())[1:-1]:  # iterating over a list of tuples, each containing a key and value
                if value != "":
                    workout_history = f"{workout_history}\n{key}: "  # first part of addition

                    value = ast.literal_eval(value)  # convert str rep. of list into actual list

                    for i in value:  # for every set of an exercise
                        workout_history = f"{workout_history}\n({i[0]}, {i[1]})"  # second part of addition

            if obj["Comment"] != "": # if the user wrote a comment for this workout
                workout_history = f"{workout_history}\nComment: {obj['Comment']}" # add comment to the string

            workout_history = f"{workout_history}\n\n"

        return workout_history

    def show_past_workouts(self):
        self.ids.feedback_label.text = ""  # clear feedback_label if button pressed
        self.edit_or_show(True)  # configure widgets (showing mode)

        if self.ids.workout_spinner.text != "Select Workout":  # workout must be selected
            self.ids.main_label.text = self.get_workouts_str(self.ids.workout_spinner.text)

        else: # no workout selected
            self.ids.feedback_label.text = "Please select a Workout."
            self.ids.feedback_label.color = 1, 0, 0, 1

    def show_editor(self):
        app = App.get_running_app()  # for get_data_path
        self.ids.feedback_label.text = ""  # clear feedback_label if button pressed

        if self.ids.workout_spinner.text != "Select Workout":  # workout must be selected
            dict_list = []
            date_list = []

            # get workout dates
            with open(app.get_data_path(f"{self.ids.workout_spinner.text}.csv"), "r") as file:
                dictreader = csv.DictReader(file, delimiter=";")
                for obj in dictreader:
                    dict_list.append(obj)

                sorted_list = sorted(dict_list, key=lambda x: datetime.strptime(x["Date"], "%d/%m/%Y"), reverse=True)

                for obj in sorted_list:
                    date_list.append(obj["Date"])

            self.ids.date_spinner.values = date_list
            self.edit_or_show(False)  # configure widgets (editing mode)

        else: # no workout selected
            self.ids.feedback_label.text = "Please select a Workout."
            self.ids.feedback_label.color = 1, 0, 0, 1

    # checks whether date has been selected
    def on_date_selected(self):
        if self.ids.date_spinner.text == "Select Date": # no date selected yet
            return

        else:
            whole_history = self.get_workouts_str(self.ids.workout_spinner.text) # get str with entire workout history
            this_workout = re.findall(
                fr"(Date: {re.escape(self.ids.date_spinner.text)}.+?)(?=Date:|\Z)",
                whole_history, re.DOTALL) # extract the selected workout
            str_without_date = re.sub(r"Date: (\d\d/\d\d/\d\d\d\d)", "", this_workout[0]) # remove date
            self.ids.edit_box.text = str_without_date.strip() # show

    def parse_new_str(self):
        app = App.get_running_app()  # for get_data_path
        new_dict = {}
        new_str = self.ids.edit_box.text # get the edited string

        try:
            new_dict.update({"Date": self.ids.date_spinner.text})

            exer_matches = re.findall(r"(\w+:\s?\n(?:\(\d+\sKG,\s?\d+\sReps\)\n?)+)", new_str, re.DOTALL) # find exercises + sets
            new_str = re.sub(r"(\w+:\s?\n(?:\(\d+\sKG,\s?\d+\sReps\)\n?)+)", "", new_str)

            for match in exer_matches:
                name_match = re.search(r"(\w+):", match) # find exercise name
                new_str = re.sub(re.escape(name_match.group(1)), "", new_str) # remove current exercise name

                set_iter = re.finditer(r"\((\d+\sKG),\s?(\d+\sReps)\)", match) # returns iterable
                set_matches = []
                for s in set_iter:
                    set_matches.append([s.group(1), s.group(2)]) # collect weight and reps
                    new_str = re.sub(re.escape(s.group(0)), "", new_str) # remove current sets

                new_dict.update({name_match.group(1): str(set_matches)})

            comment_match = re.search(r"Comment:\s?(.+)", new_str) # find comment
            if comment_match != None:
                new_dict.update({"Comment": comment_match.group(1)})
            new_str = re.sub(r"Comment:\s?(.+)?", "", new_str)  # remove comment

            # filling missing keys (exercises or comment)
            with open(app.get_data_path(f"{self.ids.workout_spinner.text}.csv"), "r") as file:
                dictreader = csv.DictReader(file, delimiter=";")
                fieldnames = dictreader.fieldnames # get fieldnames to compare to exercise keys

            for obj in fieldnames:
                if obj not in new_dict.keys():
                    new_dict.update({obj: ''}) # add missing key and empty str as value

            if new_str.strip() == "": # should be empty if edits are valid
                self.replace_workout(new_dict) # move on to next method

            else:
                self.ids.edit_feedback.text = f"Invalid edits. Hint:\n{new_str}"
                self.ids.edit_feedback.color = 1, 0, 0, 1

        except Exception as e:
            print(e)
            self.ids.edit_feedback.text = "Invalid."
            self.ids.edit_feedback.color = 1, 0, 0, 1

    def replace_workout(self, new_dict):
        app = App.get_running_app()  # for get_data_path
        workout_list = []

        with open(app.get_data_path(f"{self.ids.workout_spinner.text}.csv"), "r") as file:
            dictreader = csv.DictReader(file, delimiter=";")
            for row in dictreader:
                workout_list.append(row)

        for obj in workout_list:
            if obj["Date"] == new_dict["Date"]: # find edited workout (based on date)
                workout_list[workout_list.index(obj)] = new_dict # replace workout (dict) in list
                break

        # checking if all workouts have the same exercises
        for obj in workout_list:
            if obj.keys() != new_dict.keys():
                self.ids.edit_feedback.text = "Invalid. Hint:\nCheck exercise names."
                self.ids.edit_feedback.color = 1, 0, 0, 1
                return

        fieldnames = new_dict.keys()

        with open(app.get_data_path(f"{self.ids.workout_spinner.text}.csv"), "w", newline="") as file:
            dictwriter = csv.DictWriter(file, delimiter=";", fieldnames=fieldnames)
            dictwriter.writeheader()
            for obj in workout_list:
                dictwriter.writerow(obj)

        self.ids.edit_feedback.text = ("Changes saved!")
        self.ids.edit_feedback.color = 0, 1, 0, 1

    def edit_or_show(self, showing_mode):
        if showing_mode: # True as parameter -> showing mode
            self.ids.main_label.disabled = False
            self.ids.main_label.opacity = 1
            self.ids.main_label.height = self.ids.main_label.texture_size[1]
            self.ids.main_label.size_hint_y = None

            for wid in [self.ids.edit_box, self.ids.apply_btn, self.ids.edit_feedback, self.ids.date_spinner]:
                wid.opacity = 0
                wid.disabled = True
                wid.height = 0
                wid.size_hint_y = None


        else: # False as parameter -> editing mode
            self.ids.main_label.disabled = True
            self.ids.main_label.opacity = 0
            self.ids.main_label.height = 0
            self.ids.main_label.size_hint_y = None

            for wid in [self.ids.edit_box, self.ids.apply_btn, self.ids.edit_feedback, self.ids.date_spinner]:
                wid.opacity = 1
                wid.disabled = False
                wid.height = wid.minimum_height if hasattr(wid, "minimum_height") else 50
                wid.size_hint_y = None


class DelWrkPopup(Popup):
    # deleting the selected workout
    def del_workout(self):
        app = App.get_running_app()  # for get_data_path

        os.remove(app.get_data_path(f"{self.workout}.csv")) # delete workout-specific file

        self.workout_list.remove(self.workout) # remove workout name from workout_list
        with open(app.get_data_path("all_workouts.csv"), "w", newline="") as file: # open in writing mode to overwrite
            writer = csv.writer(file)
            writer.writerow(["Workouts"]) # write header
            for obj in self.workout_list:
                writer.writerow([obj]) # add every remaining workout


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
        sm.add_widget(AddWrkScreen(name="addwrk"))
        sm.add_widget(DelWrkScreen(name="delwrk"))
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
            self.open_warning() # open warning_popup
            return True # prevent closing of the app (default behaviour)
        else: # other button pressed
            return False

    def open_warning(self):
        popup = WarningPopup()
        popup.open()

    # return a list with all the currently saved workouts
    def get_workouts(self):

        self.workout_list = []

        with open(self.get_data_path("all_workouts.csv"), "r") as file:
            reader = csv.reader(file)
            next(reader)  # skip header ("Workouts")
            for line in reader:
                for obj in line:  # iterating over each of the lists to get individual strings
                    self.workout_list.append(obj)  # append all available exercises to list

        return self.workout_list  # return list


# running the app
if __name__ == "__main__":
    Powerpath().run()
