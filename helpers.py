import os
import re
import qrcode
from flask import redirect, render_template, session
from functools import wraps
from datetime import datetime

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def validate_license_plate(plate):
    """
    Validate a vehicle license plate format.

    Example (Brazilian format):
    - Old: ABC-1234
    - New: ABC1D23
    """
    pattern = r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$"  # Brazilian format
    if not re.match(pattern, plate):
        return False
    return True

def format_date(date_str):
    """
    Format a date string (YYYY-MM-DD) into a human-readable format.

    Example:
    - Input: "2024-11-24"
    - Output: "24/11/2024"
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def generate_qr(data, output_path="static/qrcodes"):
    """
    Generate a QR Code for the given data and save it as an image file.

    Args:
    - data: The content to encode in the QR Code.
    - output_path: Directory to save the QR Code image.

    Returns:
    - The file path of the saved QR Code.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Gerar um nome de arquivo seguro
    file_name = f"{data.replace('/', '_')}.png"  # Substituir '/' por '_'
    file_path = os.path.join(output_path, file_name)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_path)

    return file_path


