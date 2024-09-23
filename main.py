import PySimpleGUI as sg
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
import subprocess
import os

''' if using Ali PC use this in ENV
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=july5_123$geolp
DB_NAME=alidb
'''

'''' config when building app for sim computer
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=july6_123$geolp
DB_NAME=serieldb
'''

# When exported and running on Sim PC use this:
'''
DB_HOST=192.168.4.116
DB_USER=geolabelcomp3
DB_PASSWORD=geo_123$3
DB_NAME=alidb
'''



# Load environment variables from .env file
load_dotenv()

# MySQL connection setup
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Connect to MySQL
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Set PySimpleGUI theme to default
sg.theme('Default1')

# Define the path to your image
image_path = "logo.png"  # Update this to the path of your image




######################  Text file reading Start ######################


def read_carrier_text():
    carrier_array = []

    # read the text from file
    with open('Carrier.txt', 'r') as file:
        data = file.read()
        carrier_array = [string.strip() for string in data.split("\n") if string.strip()]
        print(f"Extracted QR strings: {carrier_array}\n")
    carrier_array.sort()
    return carrier_array



def read_qr_strings_from_file():
    qr_strings = []

    # Read the QR strings from 'Tenna_QR.txt' file
    with open('Tenna_QR.txt', 'r') as file:
        data = file.read()
        print('Here is qr raw data', data)

        # Split by '###' and strip any unnecessary whitespace
        qr_strings = [string.strip() for string in data.split('###############') if string.strip()]

        # Debug: print the extracted strings
        print(f"Extracted QR strings: {qr_strings}\n")

    return qr_strings

# Read the data from the file to populate the combo box
carrierFile = read_carrier_text()
qr_strings = read_qr_strings_from_file()

######################  Text file reading End ######################







###################### Program Features ######################
def view_last_esn(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM current_esn")
    rows = cursor.fetchall()
    cursor.close()

    # Ensure rows is non-empty
    if not rows:
        rows = [['', '', '', '','']]  # Provide a default empty row with the correct number of columns

    # Convert each row from tuple to list and prepend row number starting from 1
    rows = [[i + 1] + list(row) for i, row in enumerate(rows)]

    # Define table headings with Row number
    headings = ['Row', 'Serial', 'Carrier', 'Fuel ID','QR']

    # Return the layout for the pop-up window
    return [
        [sg.Table(
            values=rows,
            headings=headings,
            display_row_numbers=False,  # We handle row numbers manually
            auto_size_columns=False,  # Disable auto column sizing
            col_widths=[5, 13, 9, 9,40],  # Set specific column widths
            num_rows=min(25, len(rows)),  # Set number of rows to show at once
            size=(600, 400),  # Increase the table size (width, height)
            justification='center',
            header_background_color="#305c9c",
            alternating_row_color='#E5E4E2',
            header_text_color='white',



        )]
    ]

# need to fix pop length
def repeat_print(conn):
    # Define the layout of the window
    layout = [
        [sg.Text('Enter Serial Numbers (one per line):')],
        [sg.Multiline(size=(40, 10), key='-SERIAL_NUMBERS-')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]

    window = sg.Window('Reprint Serial Numbers', layout)

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Cancel'):
            window.close()
            return

        if event == 'Submit':
            serial_numbers = values['-SERIAL_NUMBERS-'].strip().split('\n')
            if not serial_numbers:
                sg.popup('No serial numbers entered. Please enter at least one serial number.')
                continue

            # Create a cursor object
            cursor = conn.cursor()

            # First, move all data from current_esn to archive_esn regardless of the input
            cursor.execute(
                "INSERT INTO archive_esn (serial_number, carrier, fuel_id) SELECT serial_number, carrier, fuel_id FROM current_esn"
            )
            cursor.execute("DELETE FROM current_esn")
            conn.commit()

            # Initialize a flag to track if any serial number fails to be processed
            all_successful = True

            for serial_number in serial_numbers:
                serial_number = serial_number.strip()
                if not serial_number:
                    continue

                # Check if the serial number exists in archive_esn
                cursor.execute("SELECT serial_number FROM archive_esn WHERE serial_number = %s", (serial_number,))
                result = cursor.fetchone()

                if result:
                    # Move the serial number from archive_esn to current_esn
                    cursor.execute(
                        "INSERT INTO current_esn (serial_number, carrier, fuel_id) SELECT serial_number, carrier, fuel_id FROM archive_esn WHERE serial_number = %s",
                        (serial_number,))
                    cursor.execute("DELETE FROM archive_esn WHERE serial_number = %s", (serial_number,))
                    conn.commit()
                else:
                    # Set the flag to False if any serial number is not found
                    all_successful = False
                    break

            # Display a message based on the success status
            if all_successful:
                sg.popup('All serial numbers were successfully processed.')
            else:
                sg.popup('Some serial numbers could not be processed.')

            cursor.close()
            window.close()
            return


######################  Program Features End ######################








######################  Future Menu Functions  #######################
def help():
    return [
        [sg.Text('This App generates serial numbers.')],
        [sg.Button('Close')]
    ]

######################  Future Menu Functions End #######################


####################### layout for windows
def open_popup(layout, title):
    window = sg.Window(title, layout, modal=True)
    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, 'Close'):
            break
    window.close()



######################  Home Page #######################
# Main window layout
# Set the global icon
sg.set_options(icon="appico.ico")
layout = [
    [sg.Menu([['Menu', ['Help']]])],
    [sg.Text("                       "), sg.Image(filename=image_path, size=(100, 100)),
     sg.Text("Geometris Serial Manager Application", font=('Arial', 16))],  # Add the image to the layout
    [sg.Text('Enter 3-digit model:     ', font=('Arial', 12)),
     sg.InputText(key='-MODEL-', size=(5, 2), font=('Arial', 30))],
    [sg.Text('Enter number (from):   ', font=('Arial', 12)),
     sg.InputText(key='-FROM-', size=(25, 2), font=('Arial', 30))],
    [sg.Text('Enter number (to):       ', font=('Arial', 12)),
     sg.InputText(key='-TO-', size=(25, 2), font=('Arial', 30))],
    [sg.Text('Select Carrier:             ', font=('Arial', 12)),
     sg.Combo(carrierFile, key='-CARRIER-', readonly=True, font=('Arial', 30), size=(25, 10))],
    [sg.Text('Fuel ID:                         ', font=('Arial', 12)),
     sg.Combo(['Yes', 'No'], key='-FUELID-', readonly=True, font=('Arial', 30), size=(25, 2))],
    [sg.Text('QR Links:                     ', font=('Arial', 12)),
     sg.Combo(qr_strings, key='-qrLink-', readonly=True, font=('Arial', 12), size=(25, 10))],

    [sg.Button('Submit', font=('Arial', 15),size=(15,2), border_width=2, bind_return_key=True,button_color=('white','#305c9c'),mouseover_colors='gray'),
     sg.Button('View Last Print', font=('Arial', 15),size=(15,2),border_width=2,mouseover_colors='gray'),
    sg.Button('Reprint', font=('Arial', 15),size=(15,2),border_width=2,mouseover_colors='gray'),
     ],
    [sg.Text('Status:', font=('Arial', 12))],
    [sg.Multiline(size=(80, 10), key='-STATUS-', font=('Arial', 12), disabled=True,background_color="#C0C0C0",sbar_frame_color="#305c9c")],
    [sg.Text('www.geometris.com', font=('Arial', 8),)],
]

window = sg.Window('Serial Manager June 16 2024', layout,icon='appico.ico')




######################  Function to validate user input ####################### add excpetion of not printing above 1k or 12 digit max
def validate_inputs(model, from_num, to_num):
    try:
        from_num = int(from_num)
        to_num = int(to_num)
    except ValueError:
        raise ValueError("The 'from' and 'to' values must be integers.")

    if from_num > to_num:
        raise ValueError("The 'from' number cannot be greater than the 'to' number.")

    if len(model) != 3:
        raise ValueError("The model must be exactly 3 characters long.")

    # Check if the third character of the model is an alphabet
    if not model[2].isalpha():
        raise ValueError("The third digit of the model is not an alphabet.")

    # Check if the third character of the model is a lowercase letter
    if model[2].islower():
        raise ValueError("The third digit of the model must not be a lowercase letter.")

    return from_num, to_num

# generate serial and store in db
# this code creates the serial number and the fuel ID, and you need to add here
def generate_serials(model, from_num, to_num):
    day_of_year = datetime.now().timetuple().tm_yday
    serials = []
    fuel_id_array = []





    for num in range(from_num, to_num + 1):

        facility = 1
        year = 4
        num_padded = str(num).zfill(4)
        serial_number = f"{model}{facility}{year}{day_of_year:03d}{num_padded}"
        print(serial_number)
        fuel_id = f"{facility}{year}{day_of_year:03d}{num_padded}"
        print(fuel_id)
        serials.append(serial_number)
        fuel_id_array.append(fuel_id)
    return serials, fuel_id_array,

def store_serials_in_db(serials, carrier, fuel_ids=None,qr_codes=None):
    try:
        for serial_number in serials:
            cursor.execute("SELECT COUNT(*) FROM current_esn WHERE serial_number = %s", (serial_number,))
            result_current = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM archive_esn WHERE serial_number = %s", (serial_number,))
            result_archive = cursor.fetchone()
            if result_current[0] > 0:
                raise Exception(f"Duplicate serial number found in current_esn: {serial_number}")
            if result_archive[0] > 0:
                raise Exception(f"Duplicate serial number found in archive_esn: {serial_number}")

        # Move current_esn data to archive_esn
        cursor.execute("INSERT INTO archive_esn (serial_number, carrier, fuel_id,qr_code) SELECT serial_number, carrier, fuel_id,qr_code  FROM current_esn")
        cursor.execute("DELETE FROM current_esn")
        for i, serial_number in enumerate(serials):
            fuel_id = fuel_ids[i] if fuel_ids and values['-FUELID-'] == 'Yes' else None
            qr_code = qr_codes if qr_codes else None

            # print the logs
            print('This the database function log, here the esn being store:', serial_number)  # log to see what qr it is.
            print('This the database function log, here the fuelid being store:',fuel_id) # log to see what qr it is.
            print('This the database function log, here the qrcode being store:',qr_code) # log to see what qr it is.

            # store in db
            cursor.execute("INSERT INTO current_esn (serial_number, carrier, fuel_id,qr_code ) VALUES (%s, %s, %s,%s)",
                           (serial_number, carrier if carrier else None, fuel_id,qr_code))


        conn.commit()
        return True, "Serial numbers generated successfully!"
    except Exception as e:
        conn.rollback()
        return False, f"Error: {e}"

######################  Function to validate user input End #######################











######################  Run code #######################
while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break

    if event == 'Submit':
        from_num = values['-FROM-']
        to_num = values['-TO-']
        model = values['-MODEL-']
        carrier = values['-CARRIER-']
        qrCode = values['-qrLink-']  # Get the selected QR code from the dropdown
        print(qrCode)


        if not from_num or not to_num or not model or not carrier:
            window['-STATUS-'].update("input data to process...")

        try:
            if from_num and to_num and model:
                from_num, to_num = validate_inputs(model, from_num, to_num)
                serials, fuel_id_array = generate_serials(model, from_num, to_num)
                fuel_ids = fuel_id_array if values['-FUELID-'] == 'Yes' else None
                # Create a list of QR codes, one for each serial number
                qr_codes = [qrCode] * len(serials) if qrCode else None



                success, message = store_serials_in_db(serials, carrier, fuel_ids,qrCode)
                if success:
                    window['-STATUS-'].update(message + '\n' + '\n'.join(serials))
                    window['-FROM-'].update("")
                    window['-TO-'].update("")
                    window['-MODEL-'].update("")
                    window['-CARRIER-'].update("")
                    window['-FUELID-'].update("")
                    window['-qrLink-'].update("")

                    # # Popup to ask user to select a file using checkboxes
                    # layout = [
                    #     [sg.Text('Select a file:')],
                    #     [sg.Checkbox('87.bak', key='-FILE_A-', enable_events=True)],
                    #     [sg.Checkbox('78.bak', key='-FILE_B-', enable_events=True)],
                    #     [sg.Button('Open File'), sg.Button('Cancel')]
                    # ]
                    # file_window = sg.Window('Choose File', layout)
                    #
                    # selected_file = None
                    # while True:
                    #     event, values = file_window.read()
                    #     if event in (sg.WIN_CLOSED, 'Cancel'):
                    #         file_window.close()
                    #         break
                    #
                    #     # Ensure only one checkbox is selected at a time
                    #     if event in ('-FILE_A-', '-FILE_B-'):
                    #         if event == '-FILE_A-':
                    #             if values['-FILE_A-']:
                    #                 file_window['-FILE_B-'].update(False)
                    #                 selected_file = '87.bak'
                    #             else:
                    #                 selected_file = None
                    #         elif event == '-FILE_B-':
                    #             if values['-FILE_B-']:
                    #                 file_window['-FILE_A-'].update(False)
                    #                 selected_file = '78.bak'
                    #             else:
                    #                 selected_file = None
                    #
                    #     if event == 'Open File':
                    #         if selected_file:
                    #             file_path = os.path.join(os.getcwd(), selected_file)
                    #             if os.path.exists(file_path):
                    #                 try:
                    #                     subprocess.run(['start', file_path], check=True, shell=True)
                    #                 except subprocess.CalledProcessError as e:
                    #                     window['-STATUS-'].update(f"Failed to open file: {e}")
                    #             else:
                    #                 window['-STATUS-'].update(f"File {selected_file} not found.")
                    #             file_window.close()
                    #             break
                    #         else:
                    #             sg.popup("Please select a file.")
                    # file_window.close()

                else:
                    window['-STATUS-'].update(message)
        except ValueError as ve:
            window['-STATUS-'].update(f"Input Error: {str(ve)}")

    elif event == 'View Last Print':
        # Run the view_last_esn function
        layout = view_last_esn(conn)
        open_popup(layout, 'Last Print')


    elif event == 'Reprint':
        # Run the repeat_print function
        repeat_print(conn)


    elif event in ['Help']:

        if event == 'Help':
            layout = help()
            open_popup(layout, 'Help')


# Close connections
cursor.close()
conn.close()
window.close()
