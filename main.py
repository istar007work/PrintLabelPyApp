import PySimpleGUI as sg
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
import subprocess
import os
from mysql.connector.errors import Error
import csv



###### notes what to work on
# now remove the drodown qr code ,and usebox to all,


''' if using Ali PC use this in ENV
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=july5_123$geolp
DB_NAME=alidb
'''

''' if using Ali PC use this in ENV version 2 test, 
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=july5_123$geolp
DB_NAME=printlabelv2
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



#################################################################### Global entries
# Global query dictionary ***********not in use will use it later to finalize code
queries = {
    "count_current": "SELECT COUNT(*) FROM current_esn WHERE serial_number = %s", # This query checks how many entries exist in the current_esn table for a given serial_number
    "count_archive": "SELECT COUNT(*) FROM archive_esn WHERE serial_number = %s", #this checks the archive_esn table for the existence of the serial_number.
    "move_to_archive": "INSERT INTO archive_esn (serial_number, carrier, fuel_id, qr_code) SELECT serial_number, carrier, fuel_id, qr_code FROM current_esn", # this query transfers all data from the current_esn table to the archive_esn table.
    "delete_current": "DELETE FROM current_esn",
    "insert_current": "INSERT INTO current_esn (serial_number, carrier, fuel_id, qr_code) VALUES (%s, %s, %s, %s)",
    "insert_from_archive": "INSERT INTO current_esn ({columns_str}) SELECT {columns_str} FROM archive_esn WHERE serial_number = %s", # The {columns_str} placeholder allows flexibility in specifying which columns to retrieve.
    "select_from_archive": "SELECT {columns_str} FROM archive_esn WHERE serial_number = %s"
}



######################  Text file reading Start ######################

def label_count():
    # Query to count the total number of rows in the archive_esn table
    arch_count_query = 'SELECT COUNT(*) FROM archive_esn;'
    current_count_query = 'SELECT COUNT(*) FROM current_esn;'

    # Count for archive_esn
    cursor.execute(arch_count_query)
    arch_result = cursor.fetchone()  # Fetches the first row of the result
    arch_label_count = arch_result[0] if arch_result[0] is not None else 0  # Ensure it's 0 if None

    # Count for current_esn
    cursor.execute(current_count_query)
    current_result = cursor.fetchone()  # Fetches the first row of the result
    current_label_count = current_result[0] if current_result[0] is not None else 0  # Ensure it's 0 if None

    # Calculate total label count
    total_count = arch_label_count + current_label_count

    print(f'Total number of rows in archive_esn: {arch_label_count}')
    print(f'Total number of rows in current_esn: {current_label_count}')
    print(f'Total labels: {total_count}')

    return total_count  # Return the total count



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
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM current_esn")
        rows = cursor.fetchall()
        cursor.close()

        # Ensure rows is non-empty
        if not rows:
            rows = [['', '', '', '', '', '']]  # Provide a default empty row with the correct number of columns (including date)

        # Convert each row from tuple to list and prepend row number starting from 1
        rows = [[i + 1] + list(row) for i, row in enumerate(rows)]

        # Define table headings with Row number and updated columns including Date
        headings = ['Row', 'Date', 'Serial', 'Carrier', 'Fuel ID', 'QR']

        # Return the layout for the pop-up window
        return [
            [sg.Table(
                values=rows,
                headings=headings,
                display_row_numbers=False,  # We handle row numbers manually
                auto_size_columns=False,  # Disable auto column sizing
                col_widths=[5, 12, 13, 9, 9, 40],  # Adjust column widths to include Date
                num_rows=min(25, len(rows)),  # Set number of rows to show at once
                size=(700, 400),  # Adjust table size (width, height) to fit the new column
                justification='center',
                header_background_color="#305c9c",
                alternating_row_color='#E5E4E2',
                header_text_color='white',
            )]
        ]
    except mysql.connector.Error as err:
        sg.popup_error(f"Database error: {str(err)}")  # Display any database errors
        return []  # Return empty if error


def repeat_print(conn):
    # Define the layout of the window
    layout = [
        [sg.Text('This will reprint existing serial numbers or create new ones if they do not exist.')],
        [sg.Text('Enter Serial Numbers (one per line):')],
        [sg.Multiline(size=(60, 10), key='-SERIAL_NUMBERS-')],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]

    window = sg.Window('Reprint or Create Serial Numbers', layout)

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

            # First, move all data from current_esn to archive_esn
            cursor.execute(
                "INSERT INTO archive_esn (date, serial_number, carrier, fuel_id, qr_code) "
                "SELECT date, serial_number, carrier, fuel_id, qr_code FROM current_esn"
            )
            cursor.execute("DELETE FROM current_esn")
            conn.commit()

            # Initialize lists to track processing status
            valid_serials = []
            invalid_serials = []
            failed_serials = []
            newly_created_serials = []

            for serial_number in serial_numbers:
                serial_number = serial_number.strip()
                if not serial_number:
                    continue

                # Check if the serial number has exactly 12 characters
                if len(serial_number) != 12:
                    invalid_serials.append(serial_number)
                    continue

                try:
                    # Check if the serial number exists in archive_esn
                    cursor.execute("SELECT serial_number FROM archive_esn WHERE serial_number = %s", (serial_number,))
                    result_archive = cursor.fetchone()

                    # Check if the serial number exists in current_esn
                    cursor.execute("SELECT serial_number FROM current_esn WHERE serial_number = %s", (serial_number,))
                    result_current = cursor.fetchone()

                    if result_archive:
                        # If found in archive_esn, move it to current_esn
                        cursor.execute(
                            "INSERT INTO current_esn (date, serial_number, carrier, fuel_id, qr_code) "
                            "SELECT date, serial_number, carrier, fuel_id, qr_code FROM archive_esn WHERE serial_number = %s",
                            (serial_number,)
                        )
                        cursor.execute("DELETE FROM archive_esn WHERE serial_number = %s", (serial_number,))
                        valid_serials.append(serial_number)

                    elif result_current:
                        # If already exists in current_esn, no need to move or create
                        valid_serials.append(serial_number)

                    else:
                        # If serial doesn't exist in either, create a new record in current_esn
                        cursor.execute(
                            "INSERT INTO current_esn (date, serial_number) VALUES (NOW(), %s)",
                            (serial_number,)
                        )
                        newly_created_serials.append(serial_number)
                        valid_serials.append(serial_number)

                    conn.commit()

                except mysql.connector.Error as e:
                    failed_serials.append(serial_number)

            cursor.close()

            # Build the final popup message based on success/failure
            message = ""
            if invalid_serials:
                message += f'Invalid serial numbers (not 12 digits): {len(invalid_serials)}\n'
            if failed_serials:
                message += f'Failed serial numbers (database errors): {len(failed_serials)}\n'
            if valid_serials:
                message += f'Successfully processed serial numbers: {len(valid_serials)}\n'
            if newly_created_serials:
                message += f'New serial numbers created: {len(newly_created_serials)}\n'
                message += "These serial numbers didn't exist in the database but have been created for you.\n"

            if not message:
                message = 'All serial numbers were successfully processed.'

            # Display one popup at the end
            sg.popup(message)

            window.close()
            return


# add qr codes to database
def add_qrCodes():
    # Define the layout of the window
    layout = [
        [sg.Text('Upload a text file with QR codes')],
        [sg.Input(key='-FILE-', enable_events=True), sg.FileBrowse(file_types=(("Text Files", "*.txt"),))],
        [sg.ProgressBar(max_value=100, orientation='h', size=(35, 20), key='-PROGRESS-', visible=False,
                        bar_color=('#2c5c9d', '#DAD9D5'))],
        [sg.Button('Submit'), sg.Button('Cancel')]
    ]

    window = sg.Window('Upload QR Codes', layout)

    upload_in_progress = False

    while True:
        event, values = window.read(timeout=100)  # Timeout added to make the interface responsive

        if event in (sg.WIN_CLOSED, 'Cancel'):
            break

        if event == 'Submit':
            file_path = values['-FILE-']
            if not file_path:
                sg.popup('Please select a file to upload.')
                continue

            # Read the file contents
            try:
                with open(file_path, 'r') as file:
                    qr_codes = file.read().splitlines()
            except Exception as e:
                sg.popup(f"Error reading file: {e}")
                continue

            if not qr_codes:
                sg.popup('The file is empty. Please upload a valid file.')
                continue

            # Get the current date for qr_code_date
            qr_code_date = datetime.now().strftime('%Y-%m-%d')

            # Check for duplicates before uploading
            duplicate_qr_codes = []
            non_duplicate_qr_codes = []

            try:
                for qr_code in qr_codes:
                    cursor.execute("SELECT COUNT(*) FROM tenna_qr WHERE qr_code = %s", (qr_code,))
                    result = cursor.fetchone()
                    if result[0] > 0:
                        duplicate_qr_codes.append(qr_code)
                    else:
                        non_duplicate_qr_codes.append(qr_code)
            except Exception as e:
                sg.popup(f"Database error while checking duplicates: {e}")
                continue

            # If duplicates are found, show a popup with duplicates
            if duplicate_qr_codes:
                sg.popup(f"Duplicate QR codes found. Please check file and upload again.", title="Alert",
                         keep_on_top=True)
                continue

            if not non_duplicate_qr_codes:
                sg.popup("No new QR codes to upload.", title="No New Data")
                continue

            # Show the progress bar while pushing non-duplicate data
            window['-PROGRESS-'].update(visible=True)
            window.refresh()

            total_count = len(non_duplicate_qr_codes)
            success_count = 0
            upload_in_progress = True

            try:
                for i, qr_code in enumerate(non_duplicate_qr_codes):
                    # Check if the user clicked "Cancel" during the upload
                    event, _ = window.read(timeout=0)
                    if event == 'Cancel':
                        sg.popup('Upload interrupted by user.', title='Alert')
                        break

                    # Insert the data into MySQL
                    cursor.execute(
                        "INSERT INTO tenna_qr (qr_code_date, qr_code) VALUES (%s, %s)",
                        (qr_code_date, qr_code)
                    )
                    conn.commit()

                    # Update progress bar
                    progress = int((i + 1) / total_count * 100)
                    window['-PROGRESS-'].update(progress)
                    window.refresh()

                    success_count += 1

                else:  # If the loop wasn't interrupted by 'Cancel'
                    sg.popup(f"Success! {success_count} QR codes have been pushed to the database.", title='Success')
                    upload_in_progress = False
                    break

            except Exception as e:
                conn.rollback()
                sg.popup(f"Error pushing data to the database: {e}")

            # Hide progress bar after completion or interruption
            window['-PROGRESS-'].update(visible=False)

    window.close()

# count remaining QR codes with has null serial number
def count_remaining_qr():
    try:
        # Define the layout
        layout = [
            [sg.CalendarButton("Choose From Date", target='from_date', format="%Y-%m-%d", size=(15, 1)),
             sg.Input(key='from_date', size=(15, 1), disabled=True)],
            [sg.CalendarButton("Choose To Date", target='to_date', format="%Y-%m-%d", size=(15, 1)),
             sg.Input(key='to_date', size=(15, 1), disabled=True)],
            [sg.Button('Search', size=(15, 1)), sg.Button('Download CSV', size=(15, 1))],
            [sg.Text("Remaining QR codes with no serial number:", size=(40, 1), key='remaining_count')],
            [sg.Table(values=[], headings=['QR Code Date', 'QR Code', 'Serial Date', 'Serial Number', 'Batch Number'],
                      key='table', auto_size_columns=True, justification='center', num_rows=10)],
        ]

        # Create the window
        window = sg.Window('QR Code Data', layout, finalize=True, element_justification='left')

        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                break

            if event == 'Search':
                from_date = values['from_date'] if values['from_date'] else None
                to_date = values['to_date'] if values['to_date'] else None

                # Connect to the database and fetch the data
                cursor = conn.cursor()

                # Count query for QR codes with null serial numbers
                query_count = """
                SELECT COUNT(*)
                FROM tenna_qr
                WHERE serial_number IS NULL
                """
                cursor.execute(query_count)
                remaining_qr_count = cursor.fetchone()[0]

                # Query to fetch QR data with optional date range filters
                query_data = """
                SELECT qr_code_date, qr_code, serial_date, serial_number, batch_number
                FROM tenna_qr
                WHERE 1=1
                """
                params = []
                if from_date:
                    query_data += " AND qr_code_date >= %s"
                    params.append(from_date)
                if to_date:
                    query_data += " AND qr_code_date <= %s"
                    params.append(to_date)

                cursor.execute(query_data, params)
                results = cursor.fetchall()
                cursor.close()

                # If no data found in the date range, show an error popup
                if not results:
                    sg.popup_error("No data found in the specified date range.")
                else:
                    # Update remaining count text
                    window['remaining_count'].update(f"Remaining QR codes with no serial number: {remaining_qr_count}")

                    # Update table with results
                    window['table'].update(values=results)

            if event == 'Download CSV':
                from_date = values['from_date'] if values['from_date'] else None
                to_date = values['to_date'] if values['to_date'] else None

                # Fetch data again for CSV export
                cursor = conn.cursor()
                query_data = """
                SELECT qr_code_date, qr_code, serial_date, serial_number, batch_number
                FROM tenna_qr
                WHERE 1=1
                """
                params = []
                if from_date:
                    query_data += " AND qr_code_date >= %s"
                    params.append(from_date)
                if to_date:
                    query_data += " AND qr_code_date <= %s"
                    params.append(to_date)

                cursor.execute(query_data, params)
                results = cursor.fetchall()
                cursor.close()

                # If no data to export, show an error popup
                if not results:
                    sg.popup_error("No data available to export.")
                else:
                    # Save CSV
                    filename = sg.popup_get_file('Save as', save_as=True, no_window=True, file_types=(("CSV Files", "*.csv"),))
                    if filename:
                        with open(filename, 'w', newline='') as csvfile:
                            writer = csv.writer(csvfile)
                            headers = ['QR Code Date', 'QR Code', 'Serial Date', 'Serial Number', 'Batch Number']
                            writer.writerow(headers)
                            writer.writerows(results)
                        sg.popup(f"Data saved as {filename}")

        window.close()
    except mysql.connector.Error as err:
        sg.popup_error(f"Error: {err}")




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

# create the menu
menu_def = [
    ['Menu', ['Help']],
    ['Tenna', ['Count QR','Upload QR code']]
]



layout = [
    [sg.Menu(menu_def,
             disabled_text_color='gray',
             key='-MENU-',)],


    [sg.Text("                       "), sg.Image(filename=image_path, size=(100, 100)),
     sg.Text("Geometris Serial Manager Application", font=('Arial', 16))],  # Add the image to the layout
    [sg.Text('Enter 3-digit model:     ', font=('Arial', 12)),
     sg.InputText(key='-MODEL-', size=(5, 2), font=('Arial', 30))],
    [sg.Text('Enter number (from):   ', font=('Arial', 12)),
     sg.InputText(key='-FROM-', size=(25, 2), font=('Arial', 30))],
    [sg.Text('Enter number (to):       ', font=('Arial', 12)),
     sg.InputText(key='-TO-', size=(25, 2), font=('Arial', 30))],
    [sg.Text('Select Carrier:             ', font=('Arial', 12)),
     sg.Combo(carrierFile, key='-CARRIER-', readonly=True, font=('Arial', 30), size=(24, 10))],
    [sg.Text('Fuel ID:                         ', font=('Arial', 12)),
     sg.Combo(['Yes', 'No'], key='-FUELID-', readonly=True, font=('Arial', 30), size=(24, 2))],

    [sg.Text('QR Links:                     ', font=('Arial', 12)),
     sg.Combo(qr_strings, key='-qrLink-', readonly=True, font=('Arial', 12), size=(59, 10))],

    [sg.Text('QR:                              ', font=('Arial', 12)),
     sg.Checkbox('Enable QR', key='-qrLinkcheck-', font=('Arial', 12))],

    [sg.Button('Submit', font=('Arial', 15),size=(15,2), border_width=2, bind_return_key=True,button_color=('white','#305c9c'),mouseover_colors='gray'),
     sg.Button('View Last Print', font=('Arial', 15),size=(15,2),border_width=2,mouseover_colors='gray'),
    sg.Button('Reprint', font=('Arial', 15),size=(15,2),border_width=2,mouseover_colors='gray'),
     ],
    [sg.Text('Status:', font=('Arial', 12))],
    [sg.Multiline(size=(80, 10), key='-STATUS-', font=('Arial', 12), disabled=True,background_color="#C0C0C0",sbar_frame_color="#305c9c")],
    [sg.Text("Total labels today:",font=('Arial', 8),justification='center'),sg.Text(key='total_labels',font=('Arial', 8))],
]

window = sg.Window('Serial Manager November 2024', layout,icon='appico.ico', element_justification='left',finalize=True,titlebar_background_color="black")

# Update the total labels on startup
initial_count = label_count()  # Fetch initial count
window['total_labels'].update(initial_count)  # Update the label display




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

    # create the date
    label_date = datetime.now().strftime("%Y-%m-%d")
    print(label_date)



    # serial number generator
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
    return serials, fuel_id_array, label_date



# This function pushes serial to database - regular
def store_serials_in_db(serials, carrier, fuel_ids=None,qr_codes=None,label_date=None,):
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
        cursor.execute("INSERT INTO archive_esn (date,serial_number, carrier, fuel_id,qr_code) SELECT date,serial_number, carrier, fuel_id,qr_code  FROM current_esn")
        cursor.execute("DELETE FROM current_esn")
        for i, serial_number in enumerate(serials):
            fuel_id = fuel_ids[i] if fuel_ids and values['-FUELID-'] == 'Yes' else None
            qr_code = qr_codes if qr_codes else None

            # print the logs
            print('This the database function log, here the esn being store:',
                  label_date)  # log to see what qr it is.
            print('This the database function log, here the esn being store:', serial_number)  # log to see what qr it is.
            print('This the database function log, here the fuelid being store:',fuel_id) # log to see what qr it is.
            print('This the database function log, here the qrcode being store:',qr_code) # log to see what qr it is.

            # store in db
            cursor.execute("INSERT INTO current_esn (date,serial_number, carrier, fuel_id,qr_code ) VALUES (%s, %s, %s,%s,%s)",
                           (label_date,serial_number, carrier if carrier else None, fuel_id,qr_code))


        conn.commit()
        return True, "Serial numbers generated successfully!"
    except Exception as e:
        conn.rollback()
        return False, f"Error: {e} not able to push to database"




# QR FUNCTION START
# This function stores numbers with qr functionality when user hits checkbox
'''
def StoreSerialWithQRCode(serials, carrier, qrCode, label_date):
    try:


        cursor = conn.cursor()

        # Step 1: Find the latest QR code row in `tenna_qr` where serial_number is NULL
        query_find_qr = """
        SELECT qr_code
        FROM tenna_qr
        WHERE serial_number IS NULL
        ORDER BY qr_code_date DESC
        LIMIT 1
        """
        cursor.execute(query_find_qr)
        qr_code_row = cursor.fetchone()

        # If a QR code with NULL serial number is found
        if qr_code_row:
            qr_code = qr_code_row[0]

            # Step 2: Clear all data from the current_esn table before adding new serial numbers
            query_clear_current_esn = "DELETE FROM current_esn"
            cursor.execute(query_clear_current_esn)
            conn.commit()

            # Step 3: Iterate over each serial number and update both tables
            for serial_number in serials:
                # Update the found row in `tenna_qr` with the serial number and other details
                query_update_qr = """
                UPDATE tenna_qr
                SET serial_date = %s, serial_number = %s
                WHERE qr_code = %s AND serial_number IS NULL
                LIMIT 1
                """
                cursor.execute(query_update_qr, (label_date, serial_number, qr_code))
                conn.commit()

                # Insert into `current_esn` table after updating `tenna_qr`
                query_insert_current = """
                INSERT INTO current_esn (date, serial_number, carrier, qr_code)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_insert_current, (label_date, serial_number, carrier, qr_code))
                conn.commit()

            success = True
            message = "Serial numbers stored successfully in both tenna_qr and current_esn tables."

        else:
            # If no QR code with NULL serial is found, show a popup
            sg.popup("No available QR code found with a null serial number.")
            success = False
            message = "No available QR code found with a null serial number."

    except mysql.connector.Error as err:
        success = False
        message = f"Error: {str(err)}"

    finally:
        # Close the loading popup after processing is complete
        sg.popup_animated(None)  # Closes the animated popup


    return success, message
'''



# Function to process the serials and show a progress popup
def StoreSerialWithQRCode(serials, carrier, qrCode, label_date):
    try:
        # Show a progress bar (indeterminate)
        progress_bar = sg.Window(
            'Processing...',
            [[sg.Text('Please wait, generating serials...')],
             [sg.ProgressBar(1, orientation='h', size=(20, 20), key='progress',bar_color=('#2c5c9d', '#DAD9D5'))]],
            keep_on_top=True,
            finalize=True
        )

        progress_elem = progress_bar['progress']

        cursor = conn.cursor()

        # Step 1: Find the latest QR code row in `tenna_qr` where serial_number is NULL
        query_find_qr = """
        SELECT qr_code
        FROM tenna_qr
        WHERE serial_number IS NULL
        ORDER BY qr_code_date DESC
        LIMIT 1
        """
        cursor.execute(query_find_qr)
        qr_code_row = cursor.fetchone()

        # If a QR code with NULL serial number is found
        if qr_code_row:
            qr_code = qr_code_row[0]

            # Step 2: Clear all data from the current_esn table before adding new serial numbers
            query_clear_current_esn = "DELETE FROM current_esn"
            cursor.execute(query_clear_current_esn)
            conn.commit()

            # Step 3: Iterate over each serial number and update both tables
            total_serials = len(serials)
            for i, serial_number in enumerate(serials):
                # Update the progress (indeterminate, just showing movement)
                progress_elem.update_bar((i + 1) / total_serials)



                # Update the found row in `tenna_qr` with the serial number and other details
                query_update_qr = """
                UPDATE tenna_qr
                SET serial_date = %s, serial_number = %s
                WHERE qr_code = %s AND serial_number IS NULL
                LIMIT 1
                """
                cursor.execute(query_update_qr, (label_date, serial_number, qr_code))
                conn.commit()

                # Insert into `current_esn` table after updating `tenna_qr`
                query_insert_current = """
                INSERT INTO current_esn (date, serial_number, carrier, qr_code)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_insert_current, (label_date, serial_number, carrier, qr_code))
                conn.commit()

            success = True
            message = "Serial numbers stored successfully in both tenna_qr and current_esn tables."
        else:
            sg.popup("No available QR code found with a null serial number.")
            success = False
            message = "No available QR code found with a null serial number."

    except mysql.connector.Error as err:
        success = False
        message = f"Error: {str(err)}"

    finally:
        # Close the progress bar after processing
        progress_bar.close()

    return success, message


# This function pushes serial to database - when QR is checked
#It will first push to the tenna_qr table, where the serial numbers are initially stored with the QR code. After that, they will be moved to the current table.
# Logic: 1. serial number goes to qr table, and looks for the latest qr code that does not have any serial number in the same row, and then stores serial numbers there for i





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
        qrLinkCheck = values['-qrLinkcheck-']
        print(qrCode)


        if not from_num or not to_num or not model or not carrier:
            window['-STATUS-'].update("input data to process...")

        try:
            if from_num and to_num and model:
                from_num, to_num = validate_inputs(model, from_num, to_num)



                # serial, fuel_id_array,label_date are variables that will store values returned from  generate_serials function
                serials, fuel_id_array,label_date = generate_serials(model, from_num, to_num)
                print('After pressing submit log: serial: ',serials)
                print('After pressing submit log: serial: ',fuel_id_array)
                print('After pressing submit log: serial: ',label_date)

                fuel_ids = fuel_id_array if values['-FUELID-'] == 'Yes' else None

                # void below
                # Create a list of QR codes, one for each serial number
                #qr_codes = [qrCode] * len(serials) if qrCode else None


                # logic is user has checked marked QR CODE, then use the QR function
                if qrLinkCheck:
                    success, message = StoreSerialWithQRCode(serials, carrier, qrCode, label_date)

                else:
                    # push to database using the regular storing db function
                    success, message = store_serials_in_db(serials, carrier, fuel_ids, qrCode, label_date)
                # print to window when success, and clear the inputs
                if success:
                    window['-STATUS-'].update(message + '\n' + '\n'.join(serials))
                    window['-FROM-'].update("")
                    window['-TO-'].update("")
                    window['-MODEL-'].update("")
                    window['-CARRIER-'].update("")
                    window['-FUELID-'].update("")
                    window['-qrLink-'].update("")

                    window['total_labels'].update(label_count())

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

    elif event == 'Upload QR code':
        add_qrCodes()

    elif event == "Count QR":
        count_remaining_qr()


# Close connections
cursor.close()
conn.close()
window.close()
