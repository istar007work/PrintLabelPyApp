import PySimpleGUI as sg
import time

# Create the splash screen layout
splash_layout = [[sg.Text("Loading...", font=("Helvetica", 18), justification="center")]]
splash_window = sg.Window("Welcome", splash_layout, size=(300, 100), no_titlebar=True, finalize=True, keep_on_top=True)

# Show the splash screen for a few seconds
time.sleep(2)  # Display for 2 seconds
splash_window.close()

# Main application layout
main_layout = [
    [sg.Text("Welcome to the Main Application!", font=("Helvetica", 16))],
    [sg.Button("OK")]
]

# Create the main application window
main_window = sg.Window("Main Application", main_layout)

# Main event loop
while True:
    event, values = main_window.read()
    if event == sg.WINDOW_CLOSED or event == "OK":
        break

main_window.close()
