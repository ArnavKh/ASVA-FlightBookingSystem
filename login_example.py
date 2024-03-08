from flask import Flask, render_template, url_for, request, session, redirect
from pymongo import MongoClient
import bcrypt

# Instantiate the Flask class by creating a flask application
app = Flask(__name__)

# Used for securely signing the session
app.secret_key = "pm0P#!L38@bnjhTye"

# MongoDB Connection
client = MongoClient('mongodb://localhost:27017/')
db = client['Flight_Booking']
users_collection = db['User_Data']

# Landing Page for login
@app.route('/')
def index():
    # If user is already logged in, no need to prompt login again
    if 'username' in session:
        return 'You are already logged in'

    # Prompt user to login
    return redirect('/login')



@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user has entered information in the login form
    if request.method == 'POST':
        login_user = users_collection.find_one({'username': request.form['username']})

        # If a matching username is found
        if login_user:
            # If password is correct
            if bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['password']):
                session['username'] = request.form['username']
                return redirect('/loggedin')

        return 'Invalid username/password'
    
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user has entered information in the registration form
    if request.method == 'POST':
        existing_user = users_collection.find_one({'username': request.form['username']})

        # If entered data is not found in the DB
        if existing_user is None:
            # Encrypting entered password
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            # Inerting given information into DB
            users_collection.insert_one({'username': request.form['username'], 'password': hashpass})

            return redirect('/login')

        return 'Username already exists'

    return render_template('register.html')


@app.route('/loggedin')
def user():
    # If user is logged in (in session)
    if 'username' in session:
        return render_template('loggedin.html', username = session['username'])

    return redirect('/login')


@app.route('/logout', methods = ['GET', 'POST'])
def logout():
    # Remove current session
    session.pop('username', None)
    return redirect('/')

# For executing the file
if __name__ == '__main__':
    app.run(debug=True)