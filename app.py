#   flask run
#   sqlite3 finance.db
#   right-click "finance.db" and click "open in phpLiteAdmin"

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, is_pos_int, is_pos_float

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
#   DEVELOPMENT
# db = SQL("sqlite:///finance.db")
#   DEPLOYMENT
uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)


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
    """Show portfolio of stocks"""
    print("Getting ready to show portfolio of stocks")
    # Lift relevant user data from transactions table
    userdata1 = db.execute(
        "SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id=? GROUP BY symbol;",
        session["user_id"],
    )
    # Remove entries from user data where share number equals zero
    count = len(userdata1)
    userdata2 = []
    for i in range(count):
        if userdata1[i]["shares"] != 0:
            userdata2.append(userdata1[i])
    # Lift user cash from users table
    user_cash = float(
        db.execute("SELECT cash FROM users WHERE id = (?);", session["user_id"])[0][
            "cash"
        ]
    )
    # Initialize 2 lists: (i) current individual stock prices, (ii) total shares worth calculated by current stock price * no. of shares owned
    price_list = []
    total_list = []
    # Initialize total assets variable as user's current cash (to be added to later)
    assets_total = user_cash
    count = len(userdata2)
    for i in range(count):
        # Append current values to lists
        price_list.append(lookup(userdata2[i]["symbol"])["price"])
        total_list.append(userdata2[i]["shares"] * price_list[i])
        # Add shares total to total assets
        assets_total += total_list[i]
        # Convert current price to usd
        price_list[i] = usd(price_list[i])
        # Convert shares total to usd
        total_list[i] = usd(total_list[i])
    # Convert total assets to usd
    assets_total = usd(assets_total)
    # Convert user cash to usd
    user_cash = usd(user_cash)
    return render_template(
        "index.html",
        userdata2=userdata2,
        count=count,
        price_list=price_list,
        total_list=total_list,
        user_cash=user_cash,
        assets_total=assets_total,
    )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide symbol")
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("invalid symbol")
        # Check no. of shares inputted is a positive integer
        if not request.form.get("shares").isdigit() or request.form.get("shares") == "0":
            return apology("invalid shares entry")
        # Store purchase within purchases table in finance.db and subtract from user's cash
        total = -(float(quote["price"]) * int(request.form.get("shares")))
        user_cash = float(
            db.execute("SELECT cash FROM users WHERE id = (?)", session["user_id"])[0][
                "cash"
            ]
        )
        if user_cash + total >= 0:
            newCash = user_cash + total
            db.execute(
                "UPDATE users SET cash = (?) WHERE id = (?)",
                newCash,
                session["user_id"],
            )
            total = str(total)
            db.execute(
                "INSERT INTO transactions (user_id, symbol, price, shares, total, timestamp) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                session["user_id"],
                quote["symbol"],
                quote["price"],
                request.form.get("shares"),
                total,
            )
        else:
            return apology("Not enough cash")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Lift relevant user data from transactions table
    userdata = db.execute(
        "SELECT symbol, price, shares, total, timestamp FROM transactions WHERE user_id=?",
        session["user_id"],
    )
    count = len(userdata)
    # Make a list of BOUGHT/SOLD entries corresponding to each transaction
    actions = []
    for i in range(count):
        if int(userdata[i]["shares"]) > 0:
            actions.append("BOUGHT")
        else:
            actions.append("SOLD")
    # Make a list of shares entries corresponding to each transaction
    shares = []
    for i in range(count):
        shares.append(abs(int((userdata[i]["shares"]))))
    # Make a list of totals entries corresponding to each transaction
    totals = []
    for i in range(count):
        totals.append(abs(float(userdata[i]["total"])))
    return render_template(
        "history.html",
        userdata=userdata,
        actions=actions,
        shares=shares,
        totals=totals,
        count=count,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide symbol")
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Invalid symbol")
        else:
            return render_template("quoted.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Check username input not empty
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Check username not already in use
        user_list = []
        for user in db.execute("SELECT username FROM users"):
            user_list.append(user["username"])
        if request.form.get("username") in user_list:
            return apology("username already in use", 400)
        # Check password input not empty
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        # Check password confirmation not empty
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)
        # Check password & confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)
        else:
            # Input user info into users table
            username = request.form.get("username")
            password_hash = generate_password_hash(request.form.get("password"))
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                username,
                password_hash,
            )
            # Log in new user
            # Query database for username
            rows = db.execute(
                "SELECT * FROM users WHERE username = ?", request.form.get("username")
            )
            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(
                rows[0]["hash"], request.form.get("password")
            ):
                return apology("invalid username and/or password", 403)
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]
            # Redirect user to home page
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Lift relevant user data from transactions table
    userdata = db.execute(
        "SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id=? GROUP BY symbol",
        session["user_id"],
    )
    count = len(userdata)
    if request.method == "POST":
        # Check symbol has been selected
        if not request.form.get("symbol"):
            return apology("must select a symbol")
        # Check no. of shares inputted is a positive integer
        if not request.form.get("shares").isdigit() or request.form.get("shares") == "0":
            return apology("invalid shares entry")
        # Check user has owned selected stock
        owned_stock = False
        # Keep track of index where selected symbol is located
        j = 0
        for i in range(count):
            if request.form.get("symbol") == userdata[i]["symbol"]:
                owned_stock = True
                break
            j += 1
        if owned_stock == False:
            return apology("stock never owned")
        # Check user owns enough of selected stock, sell if true
        if int(userdata[j]["shares"]) >= int(request.form.get("shares")):
            quote = lookup(request.form.get("symbol"))
            shares = int(request.form.get("shares"))
            total = shares * quote["price"]
            user_cash = float(
                db.execute("SELECT cash FROM users WHERE id = (?)", session["user_id"])[
                    0
                ]["cash"]
            )
            # Update users and transactions tables
            db.execute(
                "UPDATE users SET cash = (?) WHERE id = (?)",
                user_cash + total,
                session["user_id"],
            )
            total = str(total)
            db.execute(
                "INSERT INTO transactions (user_id, symbol, price, shares, total, timestamp) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                session["user_id"],
                quote["symbol"],
                quote["price"],
                -shares,
                total,
            )
        else:
            return apology("trying to sell more shares than owned")
        return redirect("/")
    else:
        # Lift relevant user data from transactions table
        userdata = db.execute(
            "SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id=? GROUP BY symbol",
            session["user_id"],
        )
        count = len(userdata)
        return render_template("sell.html", userdata=userdata, count=count)

# Add money!
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add money to your account"""
    if request.method == "POST":
        # Check cash input is numeric and positive
        if not is_pos_float(request.form.get("cash")):
            return apology("Invalid cash entry")
        # Update users table with new amount of cash
        cash = float(request.form.get("cash"))
        user_cash = db.execute("SELECT cash FROM users WHERE id=?", session["user_id"])[
            0
        ]["cash"]
        db.execute(
            "UPDATE users SET cash = (?) WHERE id = (?)",
            user_cash + cash,
            session["user_id"],
        )
        return render_template("added.html", cash=cash)
    else:
        return render_template("add.html")
