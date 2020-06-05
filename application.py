import os

from flask import Flask, session, render_template, redirect, request, url_for, flash ,abort, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
from forms import SearchForm, RegisterForm, LoginForm, ReviewForm

import requests

from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))




### ROUTES #####





@app.route("/logout")
def logout():
    """ Log user out """
    # Forget any user ID
    session.clear()
    flash('You have successfully logged out')

    # Redirect user to login form
    return redirect("/")



@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if request.method == "POST":

        #CHECK FOR Username
        user = db.execute("SELECT * FROM member WHERE username = :username",
        {"username":form.username.data}).first()
        if user == None:
            flash("No User Exists")
            return redirect(url_for('login'))
        else:
            #Password CHECK
            if check_password_hash(user.hashed_pass, form.password.data):
                session["user_id"] = user.username
                flash("Logged In Successfully")
                next = request.form.get('next')
                if next == None or not next[0] =='/':
                    next = url_for('search')

                return redirect(next)
            else:
                flash("Incorrect Password, Please Try Again")
                return redirect(url_for('login'))

    return render_template('login.html', form=form)



@app.route("/register", methods=["GET","POST"])
def register():

    form = RegisterForm()
    if request.method == "POST":
        #check if user exists
        user = db.execute("SELECT * FROM member WHERE username = :username",
        {"username" : form.username.data}).first()
        if user != None:
            flash("Username Already Exists")
            return redirect(url_for('register'))
        if form.validate_on_submit():
            db.execute("INSERT INTO member (username, hashed_pass) VALUES (:username, :hashed_pass)",
            {"username": form.username.data, "hashed_pass": generate_password_hash(form.password.data)})
            db.commit()
            flash("Account Created Successfully, Please Log In")
            return redirect(url_for('login'))
        else:
            flash('Unknown Error')
            return redirect(url_for('register'))


    return render_template('register.html', form=form)


@app.route('/', methods=["GET","POST"])
def search():
    form = SearchForm()
    if request.method == "POST":
        #verify that there is an object
        search = "%" + form.search.data + "%"
        search = search.title()

        results = db.execute("SELECT * FROM books \
                             WHERE isbn LIKE :search \
                             OR author LIKE :search \
                             OR title LIKE :search \
                             OR year LIKE :search LIMIT 15"\
                             ,{'search': search}).fetchall()

        if len(results) < 1 :
            flash("There are no Results Found, Please Try Again")
            redirect(url_for('search'))
            # Return Error
        else:
            return render_template('search.html', form=form, results=results)


    return render_template('search.html',form=form)

@app.route('/search/<isbn>', methods=['GET','POST'])
def booksearch(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).first()
    review = db.execute("SELECT * FROM reviews WHERE booksisbn = :isbn",{"isbn":isbn}).fetchall()
    form = ReviewForm()
    if book == None :
        flash("Book Does Not Exist")
        return redirect(url_for('search'))
    if request.method == "POST":
        # Check if user is logged in, else return error



        if session.get('user_id') != None :

            user = db.execute("SELECT * FROM member \
                              WHERE username = :username"
                              ,{"username": session['user_id'] }).first()

            check = db.execute('SELECT * FROM reviews WHERE \
                                memberusername = :username AND \
                                booksisbn = :isbn',{'username': user.username, 'isbn':isbn}).first()

            if check != None:
                flash('You have already submmited a review')
                return redirect("/search/" + isbn)

            db.execute("INSERT INTO reviews (review, memberid, booksisbn, memberusername, ratings)\
                        VALUES (:review, :memberid, :booksisbn, :memberusername, :ratings)",
                        {"review": form.review.data, "memberid": user.id,
                         "booksisbn": isbn, "memberusername": user.username, "ratings":form.ratings.data })
            db.commit()
            flash("Review Successfully Posted")
            return redirect("/search/" + isbn)
        else:
            flash("Please Login To Leave a Review")
            return redirect("/search/" + isbn)
        # get session username, find the username object in db
        # add review to database with ISBN & User ID
        # Db commit

    key = os.getenv("GOODREADS_KEY")

    query = requests.get("https://www.goodreads.com/book/review_counts.json",
            params={"key": key, "isbns": isbn})
    response = query.json()
    response = response['books'][0]


    return render_template('results.html', book=book, response=response, form=form, review=review)


@app.route("/api/<isbn>", methods=['GET'])
def api_call(isbn):

    # COUNT returns rowcount
    # SUM returns sum selected cells' values
    # INNER JOIN associates books with reviews tables

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.ratings) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.isbn = reviews.booksisbn \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    # Error checking
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422

    # Fetch result from RowProxy
    tmp = row.fetchone()

    # Convert to dict
    result = dict(tmp.items())

    # Round Avg Score to 2 decimal. This returns a string which does not meet the requirement.
    # https://floating-point-gui.de/languages/python/
    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)



if __name__ == '__main__':
    app.run(debug = True)
