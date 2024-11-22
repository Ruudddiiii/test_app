import json
import requests
from requests.auth import HTTPBasicAuth
import base64
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
import random

# GitHub settings
GITHUB_USERNAME = 'Ruudddiiii'
REPO_NAME = 'TaskTravelTime'
GITHUB_TOKEN = 'ghp_Q4pyxc2N6P5Rc4LcWEO9xjGkp4n8CL0tPTF'
TASK_FILE = 'task1.json'

# GitHub API URLs
REPO_API_URL = f'https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{TASK_FILE}'
Window.clearcolor = (random.random(), random.random(), random.random(), 1)

# Function to load tasks from GitHub
def load_tasks_from_github():
    try:
        response = requests.get(REPO_API_URL, auth=HTTPBasicAuth(GITHUB_USERNAME, GITHUB_TOKEN))
        response.raise_for_status()
        file_data = response.json()
        file_content_base64 = file_data['content']
        file_content = base64.b64decode(file_content_base64).decode('utf-8')
        data = json.loads(file_content)
        return data.get('tasks', [])
    except Exception as e:
        print(f"Error loading tasks from GitHub: {e}")
        return []

# Function to update and push tasks.json to GitHub
def save_tasks_to_github(tasks):
    try:
        response = requests.get(REPO_API_URL, auth=HTTPBasicAuth(GITHUB_USERNAME, GITHUB_TOKEN))
        response.raise_for_status()
        file_data = response.json()
        sha = file_data['sha']

        json_data = json.dumps({"tasks": tasks}).encode('utf-8')
        base64_content = base64.b64encode(json_data).decode('utf-8')

        payload = {
            "message": "Update tasks.json",
            "content": base64_content,
            "sha": sha
        }

        response = requests.put(REPO_API_URL, json=payload, auth=HTTPBasicAuth(GITHUB_USERNAME, GITHUB_TOKEN))
        response.raise_for_status()
        print("Tasks successfully updated on GitHub")
    except Exception as e:
        print(f"Error saving tasks to GitHub: {e}")

class SelectableTaskItem(RecycleDataViewBehavior, BoxLayout):
    text = StringProperty()
    selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SelectableTaskItem, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [5, 5]
        self.spacing = 5
        self.size_hint_y = None
        self.height = 40  # Adjusted height for better spacing
        
        # Add a label to display the task's text
        self.label = Label(text=self.text, size_hint_y=None, height=30, halign='left', valign='middle', font_size='14sp')  # Increased font size
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)

    def refresh_view_attrs(self, rv, index, data):
        """ Refresh the view for each task item """
        self.text = data['text']
        self.label.text = self.text  # Update the label with the task text
        return super(SelectableTaskItem, self).refresh_view_attrs(rv, index, data)

# Task list display (RecycleView)
class TaskListView(RecycleView):
    def __init__(self, **kwargs):
        super(TaskListView, self).__init__(**kwargs)
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, None),  # Use None for height to allow dynamic sizing
            size_hint_y=None,
            orientation='vertical'
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))  # Bind height to task count
        self.add_widget(self.layout_manager)

    def update_tasks(self, tasks):
        """ Update task list and refresh the display """
        self.data = [{'text': task['name']} for task in tasks]
        self.layout_manager.height = len(tasks) * 50  # Set the height based on number of tasks
        self.refresh_from_data()

class TaskManagerApp(App):
    title = 'My Custom App Name'

    def build(self):
        Window.size = (355, 600)
        self.icon = '/home/ruddi/Downloads/task.png'  # Replace with your actual path

        # Main layout
        self.layout = BoxLayout(orientation='vertical', padding=[5, 5, 5, 5], spacing=5)

        # Input for new tasks
        self.new_task_input = TextInput(hint_text='Enter new task', size_hint=(1, 0.05))
        self.layout.add_widget(self.new_task_input)

        # Label for the title
        self.display_label = Label(text='SYNC', size_hint=(1, 0.1), font_size='28sp')
        self.layout.add_widget(self.display_label)

        # ScrollView to contain the task list directly on the screen
        scroll_view = ScrollView(size_hint=(1, 0.5))
        self.task_list = TaskListView(size_hint_y=None)
        self.task_list.height = 0  # Set initial height to 0; will be updated dynamically
        scroll_view.add_widget(self.task_list)
        self.layout.add_widget(scroll_view)

        # Button layout
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=[5, 0], spacing=5)

        # Add Task button
        add_task_button = Button(text='Add Task', size_hint=(0.3, 1), font_size='12sp')
        add_task_button.bind(on_press=self.add_task)
        button_layout.add_widget(add_task_button)

        # Delete Task button
        delete_task_button = Button(text='Delete Task', size_hint=(0.3, 1), font_size='12sp')
        delete_task_button.bind(on_press=self.delete_task)
        button_layout.add_widget(delete_task_button)

        # Undo Delete button
        undo_delete_button = Button(text='Undo Delete', size_hint=(0.3, 1), font_size='12sp')
        undo_delete_button.bind(on_press=self.undo_delete)
        button_layout.add_widget(undo_delete_button)

        # Save Changes button
        save_changes_button = Button(text='Save Changes', size_hint=(0.3, 1), font_size='12sp')
        save_changes_button.bind(on_press=self.save_changes)
        button_layout.add_widget(save_changes_button)

        self.layout.add_widget(button_layout)

        # Schedule task loading after the UI is ready
        Clock.schedule_once(self.load_tasks, 1)

        # List to store deleted tasks
        self.deleted_tasks = []

        return self.layout

    def load_tasks(self, dt):
        """ Load tasks from GitHub """
        self.tasks = load_tasks_from_github()
        self.task_list.update_tasks(self.tasks)
        self.update_display_label()

    def add_task(self, instance):
        """ Add a new task """
        new_task = self.new_task_input.text.strip()
        if new_task:
            self.tasks.append({"name": new_task, "completed": False})
            self.task_list.update_tasks(self.tasks)
            self.update_display_label()
            self.new_task_input.text = ''
        else:
            print("Input is empty, no task added")

    def update_display_label(self):
        """ Update the label to display all tasks """
        task_list_str = '\n'.join(task['name'] for task in self.tasks)
        self.display_label.text = task_list_str or 'Your tasks will appear here'

    def delete_task(self, instance):
        """ Delete the most recent task """
        if self.tasks:
            deleted_task = self.tasks.pop()
            self.deleted_tasks.append(deleted_task)
            self.task_list.update_tasks(self.tasks)
            self.update_display_label()
        else:
            print("No tasks to delete")

    def undo_delete(self, instance):
        """ Undo the last delete """
        if self.deleted_tasks:
            restored_task = self.deleted_tasks.pop()
            self.tasks.append(restored_task)
            self.task_list.update_tasks(self.tasks)
            self.update_display_label()
        else:
            print("No tasks to undo")

    def save_changes(self, instance):
        """ Save the current task list to GitHub """
        save_tasks_to_github(self.tasks)

if __name__ == '__main__':
    TaskManagerApp().run()
