from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.label = Label(text="Hello, Kivy!")
        button = Button(text="Click Me")

        # Bind the button press to change the label text
        button.bind(on_press=self.change_text)

        layout.add_widget(self.label)
        layout.add_widget(button)
        return layout

    def change_text(self, instance):
        self.label.text = "Button Clicked!"


if __name__ == "__main__":
    MyApp().run()
