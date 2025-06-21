 # imports
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.factory import Factory

import csv
import os.path
from datetime import datetime

# size of the window (for desktop)
Window.size = (360, 650)


class HomeScreen(Screen):
    pass


class AddScreen(Screen):
    # adding exercise after "done" has been pressed
    def add_exercise(self):

        exercise = self.ids.ex_input.text # assigning contents of ex_input to a variable

        # input should be alnum (except: " ", "()")
        if exercise.replace(" ", "").replace("(", "").replace(")", "").isalnum():
            # update feedback label (success)
            self.ids.feedback_label.color = 0, 1, 0, 1 # green
            self.ids.feedback_label.text = "Exercise added!"
            self.ids.feedback_label.bold = True

            # setting up new exercise
            if os.path.isfile(f"{exercise}.csv") is False: # if exercise file does not exist (not added yet)
                # append to all_exercises.csv
                with open("all_exercises.csv", "a", newline="") as file: # open in append mode
                    csv_writer = csv.writer(file)
                    csv_writer.writerow([exercise])
                # create new file for current exercise
                with open(f"{exercise}.csv", "a", newline="") as file:
                    dict_writer = csv.DictWriter(file, fieldnames=["Date", "Weight"])
                    dict_writer.writeheader()

            # if exercise exists already
            else:
                # update feedback label
                self.ids.feedback_label.color = 1, 0, 0, 1
                self.ids.feedback_label.text = "Exercise exists already."
                self.ids.feedback_label.bold = True

        # if empty input
        elif exercise == "":
            self.ids.feedback_label.color = 1, 0, 0, 1
            self.ids.feedback_label.text = "Please pass in an exercise."
            self.ids.feedback_label.bold = True

        # if input syntax is incorrect
        else:
            self.ids.feedback_label.color = 1, 0, 0, 1
            self.ids.feedback_label.text = "Invalid. Allowed characters: A-Z, 0-9, (), Space"
            self.ids.feedback_label.bold = True

        self.ids.ex_input.text = ""  # clearing text input


class ChoosingScreen(Screen):

    # updating spinner whenever ChoosingPage is entered
    def on_pre_enter(self, *args):
        app = App.get_running_app() # App class contains method that returns exercise list
        exercise_list = app.get_exercises()
        self.ids.ex_spinner.values = exercise_list
        self.ids.ex_spinner.text = "Select Exercise"

    # opening the deletion popup window
    def open_popup(self):
        if self.ids.ex_spinner.text != "Select Exercise": # exercise must be chosen
            popup = DelExPopup()
            popup.exercise = self.ids.ex_spinner.text # passing chosen exercise to popup
            popup.open() # open popup

    def open_set_manager(self):
        if self.ids.ex_spinner.text != "Select Exercise": # exercise must be chosen
            sm = self.manager
            mng_screen = sm.get_screen('manage')
            mng_screen.ids.mnglabel.text = self.ids.ex_spinner.text # passing on the current spinner text
            sm.transition.direction = "left"
            sm.current = "manage" # switch screen


class DelExPopup(Popup):
    # deleting the chosen exercise
    def delete_exercise(self):

        os.remove(f"{self.exercise}.csv")  # deletion of {exercise}.csv

        app = App.get_running_app()
        exercise_list = app.get_exercises() # list with all the current exercises

        for obj in exercise_list:  # iterating over list with all the exercises
            if obj == self.exercise:  # exercise found
                exercise_list.pop(exercise_list.index(obj))  # remove exercise from list

                with open("all_exercises.csv", "w", newline="") as file:  # opening in writing mode to overwrite
                    csv_writer = csv.writer(file)
                    csv_writer.writerow(["Exercise"])  # write header (passing string in list (csvwriter requirement)
                    for obj in exercise_list:
                        csv_writer.writerow([obj])  # writing down remaining exercises
                break

        self.dismiss() # close popup window


class ManageScreen(Screen):
    # open screen to add a set
    def open_addset_screen(self):
        sm = self.manager
        addset_screen = sm.get_screen('addset')
        addset_screen.exercise = self.ids.mnglabel.text # passing on the chosen exercise
        sm.transition.direction = "left"
        sm.current = "addset" # switch screen

    def open_delset_screen(self):
        sm = self.manager
        delset_screen = sm.get_screen('delset')
        delset_screen.exercise = self.ids.mnglabel.text # passing on the chosen exercise
        sm.transition.direction = "left"
        sm.current = "delset" # switch screen


class AddSetScreen(Screen):
    # hide feedback text if reopened
    def on_pre_enter(self, *args):
        self.ids.addset_feedback.text=""

    # adding a set
    def add_set(self):
        # assigning text input to local variables
        date = self.ids.set_date.text
        weight = self.ids.set_weight.text

        # check date input
        try:
            date_check = True # check variable
            datetime.strptime(date, "%d.%m.%Y")  # datetime object should be possible to create
        except ValueError:
            pass
            date_check = False

        # check weight input
        weight_check = True # check variable
        if (weight.isnumeric() is False) or (weight.strip() == ""):
            weight_check = False

        # feedback for incorrect input
        if (weight_check is False) or (date_check is False):
            self.ids.addset_feedback.color = 1, 0, 0, 1 # red
            self.ids.addset_feedback.text = "Invalid Input"

        # correct input
        else:
            with open(f"{self.exercise}.csv", "a", newline="") as file: # open exercise-specific file to edit
                dictwriter = csv.DictWriter(file, fieldnames=["Date", "Weight"])
                dictwriter.writerow({"Date": date, "Weight": weight}) # adding date and weight to csv

            self.ids.addset_feedback.color = 0, 1, 0, 1  # green
            self.ids.addset_feedback.text = "Set added!"


class DelSetScreen(Screen):
    # update spinner values on every re-enter
    def on_pre_enter(self):
        self.create_set_list()
        self.ids.delset_spinner.values = self.setstr_list

    # open popup if deletion button pressed
    def open_popup(self):
        popup = DelSetPopup()
        popup.set_dict_list = self.set_dict_list # pass on the set_dict_list
        popup.open()  # open popup

    # get a list of all the available sets of a certain exercise
    def create_set_list(self):

        self.set_dict_list = [] # list of dicts that will containin data from each set
        self.setstr_list = []  # empty list to store the set strings (!) in (for the spinner)

        with open(f"{self.exercise}.csv", "r", newline="") as file:  # open exercise-specific file in r-mode
            dictreader = csv.DictReader(file)
            for row in dictreader:
                self.set_dict_list.append(row)  # add each row to the list of dicts

        for obj in self.set_dict_list:
            self.setstr_list.append(f"{obj['Date']}, {obj['Weight']}kg") # list in spinner format



class DelSetPopup(Popup):

    def on_pre_open(self):
        pass


    def delete_set(self):
        pass


# App class
class Powerpath(App):
    def build(self):
        # initializing screen manager that contains all windows
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(AddScreen(name="add"))
        sm.add_widget(ChoosingScreen(name="choose"))
        sm.add_widget(ManageScreen(name="manage"))
        sm.add_widget(AddSetScreen(name="addset"))
        sm.add_widget(DelSetScreen(name="delset"))

        # create .csv for saving all exercises (upon first app launch)
        if os.path.isfile("all_exercises.csv") is False:
            with open("all_exercises.csv", "a", newline="") as file: # creation of all_exercises.csv
                csv_writer = csv.writer(file)
                csv_writer.writerow(["Exercise"]) # write header
        return sm

    # return a list with all the currently saved exercises
    def get_exercises(self):

        self.exercise_list = []

        with open("all_exercises.csv", "r") as file:  # opening in reading mode
            csv_reader = csv.reader(file)
            next(csv_reader)  # skip header ("Exercise")
            for line in csv_reader:  # csv_reader = list of lists
                for obj in line:  # iterating over each of the lists to get individual strings
                    self.exercise_list.append(obj)  # append all available exercises to list

        return self.exercise_list  # return list


# running the app
if __name__ == "__main__":
    Powerpath().run()
