import PySimpleGUI as sg
def release_notes():
    release_text = """
    **Geometris Serial Manager Application - Release Notes**

    **New Features:**

    1. **Create Serial Numbers for OBD and OEM:**
       - Ability to generate serial numbers for both OBD (On-Board Diagnostics) devices and OEM (Original Equipment Manufacturer) devices.

    2. **Create Serial Numbers with Carrier and Fuel ID:**
       - Users can now generate serial numbers that include both the carrier information and an optional Fuel ID. The carrier list is configurable,
        allowing users to add the carriers they want to appear in the application by updating the carrier text file in the directory.
       

    3. **Create Serial Numbers with QR Code (Exclusive to Tenna):**
       - Tenna-exclusive QR codes are now available when creating serial numbers. This feature links each serial number to a unique QR code.

    4. **View Last Printed Serial Numbers:**
       - You can easily view the last printed serial numbers along with their associated details (such as date, carrier, and QR code).

    5. **Upload a List of New QR Codes for Tenna:**
       - Upload a new list of QR codes specifically for Tenna usage, ensuring that the system has the latest set of QR codes for association with serial numbers.

    6. **Count Available QR Codes and Download List:**
       - Track how many QR codes are left for usage, with the ability to download the list of QR codes for future reference or analysis.

    7. **Reprint Serial Numbers or Create New Ones Without QR Code, Carrier, or Fuel ID:**
       - Users can reprint serial numbers from the past or generate new ones. However, new serial numbers generated in this mode will not include QR code, carrier, or fuel ID functionality.

    **Known Limitations:**
    - Newly created serial numbers that are generated without QR code, carrier, or fuel ID will not support these functionalities.
    - Ensure that uploaded QR codes are unique and Tenna-compliant.

    For further details, contact ali@geometris.com
    """

    sg.popup_scrolled(release_text, title="Release Notes", font=("Arial", 12), size=(70, 20))