import sys
from PyQt6 import QtWidgets as qtw
from PyQt6 import QtGui as qtg
from PyQt6 import QtCore as qtc
from localdb import LocalDB


class MainWindow(qtw.QWidget):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setWindowTitle("My Calendar App")
        self.resize(800, 600)

        self.db = LocalDB()
        self.events = {}

        self.load_events_from_db()

        self.calendar = qtw.QCalendarWidget()
        self.event_list = qtw.QListWidget()
        self.event_title = qtw.QLineEdit()
        self.event_category = qtw.QComboBox()
        self.event_time = qtw.QTimeEdit(qtc.QTime(8, 0))
        self.all_day_check = qtw.QCheckBox("All Day")
        self.event_detail = qtw.QTextEdit()
        self.add_button = qtw.QPushButton("Add/Update")
        self.del_button = qtw.QPushButton("Delete")
        self.all_day_check.toggled.connect(self.event_time.setDisabled)

        # Add event categories
        self.event_category.addItems(
            ["Select category...", "New...", "Work", "Meeting", "Doctor", "Family"]
        )
        # disable the first category item
        self.event_category.model().item(0).setEnabled(False)

        # app layout's
        main_layout = qtw.QHBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.calendar)
        right_layout = qtw.QVBoxLayout()
        main_layout.addLayout(right_layout)
        right_layout.addWidget(qtw.QLabel("Events on Date"))
        right_layout.addWidget(self.event_list)
        event_form = qtw.QGroupBox("Event")
        right_layout.addWidget(event_form)
        event_form_layout = qtw.QGridLayout()
        event_form.setLayout(event_form_layout)
        event_form_layout.addWidget(self.event_title, 1, 1, 1, 3)
        event_form_layout.addWidget(self.event_category, 2, 1)
        event_form_layout.addWidget(
            self.event_time,
            2,
            2,
        )
        event_form_layout.addWidget(self.all_day_check, 2, 3)
        event_form_layout.addWidget(self.event_detail, 3, 1, 1, 3)
        event_form_layout.addWidget(self.add_button, 4, 2)
        event_form_layout.addWidget(self.del_button, 4, 3)

        # size policies
        self.calendar.setSizePolicy(
            qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Expanding
        )
        self.event_list.setSizePolicy(
            qtw.QSizePolicy.Policy.Expanding, qtw.QSizePolicy.Policy.Expanding
        )

        # connections
        self.calendar.selectionChanged.connect(self.populate_list)
        self.event_list.itemSelectionChanged.connect(self.populate_form)
        self.add_button.clicked.connect(self.save_event)
        self.del_button.clicked.connect(self.delete_event)
        self.event_list.itemSelectionChanged.connect(self.check_delete_button)
        self.event_category.currentTextChanged.connect(self.on_category_change)
        self.check_delete_button()

        self.show()

    def load_events_from_db(self):
        """Load all events from the database into memory"""
        self.events = self.db.get_all_events()

    # utility and custom slots
    def clear_form(self):
        """This method goes through the fields in our form and sets them all to default values."""
        self.event_title.clear()
        self.event_category.setCurrentIndex(0)
        self.event_time.setTime(qtc.QTime(8, 0))
        self.all_day_check.setChecked(False)
        self.event_detail.setPlainText("")

    def populate_list(self):
        """Repopulate the event_list widget with the events from that day.
        It starts by clearing the list and the form.
        It then retrieves the selected date from the calendar widget using its selectedDate() method.
        """
        self.event_list.clear()
        self.clear_form()
        date = self.calendar.selectedDate()

        # Get events from database for this date
        events = self.db.get_events_for_date(date)
        self.events[date] = events  # Update local cache

        for event in events:
            time = event["time"].toString("hh:mm") if event["time"] else "All Day"
            self.event_list.addItem(f"{time}: {event['title']}")

    def populate_form(self):
        self.clear_form()
        date = self.calendar.selectedDate()
        event_number = self.event_list.currentRow()
        if event_number == -1:
            return

        events = self.events.get(date, [])
        if event_number >= len(events):
            return

        event_data = events[event_number]
        self.event_category.setCurrentText(event_data["category"])

        if event_data["time"] is None:
            self.all_day_check.setChecked(True)
        else:
            self.event_time.setTime(event_data["time"])
        self.event_title.setText(event_data["title"])
        self.event_detail.setPlainText(event_data["detail"])

    def save_event(self):
        # Validate category selection
        if self.event_category.currentText() in ["Select category...", "New..."]:
            qtw.QMessageBox.warning(
                self, "Invalid Category", "Please select a valid category."
            )
            return

        event = {
            "category": self.event_category.currentText(),
            "time": (
                None if self.all_day_check.isChecked() else self.event_time.time()
            ),
            "title": self.event_title.text(),
            "detail": self.event_detail.toPlainText(),
        }

        if not event["title"].strip():
            qtw.QMessageBox.warning(
                self, "Invalid Title", "Please enter a title for the event."
            )
            return

        date = self.calendar.selectedDate()
        event_number = self.event_list.currentRow()

        # determining if new event is and adding or an update
        if event_number == -1:  # not in event_list, so append it

            event_id = self.db.save_event(date, event)
            event["id"] = event_id
        else:  # is an update to existing event

            existing_events = self.events.get(date, [])
            if event_number < len(existing_events):
                event_id = existing_events[event_number]["id"]
                self.db.update_event(event_id, date, event)
                event["id"] = event_id

        self.populate_list()

    def delete_event(self):
        date = self.calendar.selectedDate()
        row = self.event_list.currentRow()

        if row == -1:
            return

        events = self.events.get(date, [])
        if row < len(events):
            event_id = events[row]["id"]

            # Confirm deletion
            reply = qtw.QMessageBox.question(
                self,
                "Delete Event",
                "Are you sure you want to delete this event?",
                qtw.QMessageBox.StandardButton.Yes | qtw.QMessageBox.StandardButton.No,
                qtw.QMessageBox.StandardButton.No,
            )

            if reply == qtw.QMessageBox.StandardButton.Yes:

                self.db.delete_event(event_id)
                self.event_list.setCurrentRow(-1)
                self.clear_form()
                self.populate_list()

    def check_delete_button(self):
        self.del_button.setDisabled(self.event_list.currentRow() == -1)

    def add_category(self, category):
        self.event_category.addItem(category)
        self.event_category.setCurrentText(category)

    def on_category_change(self, text):
        if text == "New...":
            dialog = CategoryWindow(self)
            dialog.submitted.connect(self.add_category)
            self.event_category.setCurrentIndex(0)


class CategoryWindow(qtw.QDialog):

    submitted = qtc.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Add New Category")
        self.resize(300, 120)

        self.setLayout(qtw.QVBoxLayout())
        self.layout().addWidget(qtw.QLabel("Please enter a new category name:"))
        self.category_entry = qtw.QLineEdit()
        self.layout().addWidget(self.category_entry)

        button_layout = qtw.QHBoxLayout()
        self.submit_button = qtw.QPushButton("Submit")
        self.cancel_button = qtw.QPushButton("Cancel")
        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)
        self.layout().addLayout(button_layout)

        # Connect signals
        self.submit_button.clicked.connect(self.on_submit)
        self.cancel_button.clicked.connect(self.reject)
        self.category_entry.returnPressed.connect(self.on_submit)

    def on_submit(self):
        category_text = self.category_entry.text().strip()
        if category_text:
            self.submitted.emit(category_text)
            self.accept()
        else:
            qtw.QMessageBox.warning(
                self, "Invalid Category", "Please enter a category name."
            )


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec())
