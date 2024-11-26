import qrcode
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, generate_qr


# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)

app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure Library to use SQLite database
db = SQL("sqlite:///database.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    """Show all cars for the logged-in user"""
    # Obter o ID do usuário logado
    user_id = session["user_id"]

    # Consultar apenas os carros do usuário logado
    cars = db.execute(
        "SELECT id, license_plate, model, year FROM cars WHERE user_id = ? ORDER BY id DESC",
        user_id
    )
    return render_template("index.html", cars=cars)

@app.route("/history/<int:car_id>")
@login_required
def history(car_id):
    """Show history of a specific car"""
    # Consulta o histórico do carro pelo ID
    history = db.execute(
        "SELECT description, date FROM history WHERE car_id = ? ORDER BY date DESC",
        car_id
    )
    return render_template("history.html", history=history, car_id=car_id)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?",
            request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new employee"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)
        elif not password:
            return apology("must provide password", 400)
        elif password != confirmation:
            return apology("password do not match", 400)

        try:
            user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                username, generate_password_hash(password)
            )
        except ValueError:
            return apology("username already taken", 400)

        session["user_id"] = user_id
        return redirect("/")
    else:
        return render_template("register.html")

from helpers import apology, login_required, generate_qr

@app.route("/add_car", methods=["GET", "POST"])
@login_required
def add_car():
    """Add a new car for the logged-in user"""
    if request.method == "POST":
        license_plate = request.form.get("license_plate").strip().upper()
        model = request.form.get("model")
        year = request.form.get("year")
        user_id = session["user_id"]

        # Verificar se a placa já existe
        existing_car = db.execute(
            "SELECT * FROM cars WHERE license_plate = ? AND user_id = ?",
            license_plate, user_id
        )
        if existing_car:
            return apology("Car with this license plate already exists", 400)

        # Inserir o carro no banco para obter o ID
        car_id = db.execute(
            "INSERT INTO cars (license_plate, model, year, user_id, qr_code_path) VALUES (?, ?, ?, ?, ?)",
            license_plate, model, year, user_id, None
        )

        # Gerar o QR Code usando a função helpers.generate_qr
        qr_data = f"http://127.0.0.1:5000/history/{car_id}"  # Dados do QR Code
        qr_code_path = generate_qr(qr_data, "static/qrcodes")

        # Atualizar caminho do QR Code no banco
        db.execute(
            "UPDATE cars SET qr_code_path = ? WHERE id = ?",
            qr_code_path, car_id
        )

        flash("Car added successfully!")
        return redirect("/")
    else:
        return render_template("add_car.html")




@app.route("/history/<int:car_id>", methods=["GET"])
@login_required
def show_history(car_id):
    """Show maintenance history for a specific car"""
    # Obter o ID do usuário logado
    user_id = session["user_id"]

    # Garantir que o carro pertence ao usuário logado
    car = db.execute(
        "SELECT id FROM cars WHERE id = ? AND user_id = ?",
        car_id, user_id
    )
    if not car:
        return apology("You do not have access to this car", 403)

    # Consultar o histórico de manutenção
    history = db.execute(
        "SELECT date, description FROM history WHERE car_id = ? ORDER BY date DESC",
        car_id
    )
    return render_template("history.html", car_id=car_id, history=history)


@app.route("/add_history/<int:car_id>", methods=["POST"])
@login_required
def add_history(car_id):
    """Add maintenance record for a car"""
    description = request.form.get("description")
    user_id = session["user_id"]

    # Verificar se o carro pertence ao usuário logado
    car = db.execute(
        "SELECT id FROM cars WHERE id = ? AND user_id = ?",
        car_id, user_id
    )
    if not car:
        return apology("You do not have access to this car", 403)

    if not description:
        return apology("Must provide maintenance details", 400)

    # Inserir histórico no banco de dados
    db.execute(
        "INSERT INTO history (car_id, description) VALUES (?, ?)",
        car_id, description
    )

    flash("Maintenance record added successfully!")
    return redirect(f"/history/{car_id}")


@app.route("/qrcode/<int:car_id>")
@login_required
def qrcode(car_id):
    """Display QR Code for a specific car"""
    user_id = session["user_id"]

    # Verificar se o carro pertence ao usuário logado
    car = db.execute(
        "SELECT qr_code_path FROM cars WHERE id = ? AND user_id = ?",
        car_id, user_id
    )
    if not car:
        return apology("You do not have access to this car", 403)

    qr_code_path = car[0]["qr_code_path"]
    return render_template("qrcode.html", qr_code_path=qr_code_path)



if __name__ == "__main__":
    app.run(debug=True)
