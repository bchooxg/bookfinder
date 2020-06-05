import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv

load_dotenv()


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#db.execute("INSERT INTO user (username, hashed_pass) VALUES (user1, hashedpass)")


#db.execute("INSERT INTO member (username, hashed_pass) VALUES (:username, :hashed_pass)",
#                    {"username":'test1',
#                     "hashed_pass":'password'})
#print('added')
#db.commit()
search = "%" + "steve jobs" + "%"
search = search.title()

results = db.execute("SELECT isbn, author, title, year FROM books \
                      WHERE isbn LIKE :search \
                      OR author LIKE :search \
                      OR title LIKE :search \
                      OR year LIKE :search LIMIT 15"\
                      ,{'search': search}).fetchall()

print(results[0].isbn)
