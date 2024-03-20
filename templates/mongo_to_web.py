from flask import Flask, render_template, request, flash, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_paginate import Pagination
from datetime import datetime
import bcrypt
import time
import secrets



app = Flask(__name__)
app.config['SECRET_KEY'] = '@\x9d1$\xff\x87\xddTb\x8elg'    

# Connect to MongoDB
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['flight_records'] 
cities_collection = db['flight_seats']


client = MongoClient('mongodb://localhost:27017/')
db = client['Flight_Booking']
users_collection = db['User_Data']


passenger_client = MongoClient('mongodb://localhost:27017/')
passenger_db = passenger_client['Flight_Booking']
passenger_collection = passenger_db['Passenger_Data']




# Home page
@app.route("/")
def index():
    # Check if user is logged in
    if 'email' in session:
        # User is logged in, show profile option
        return render_template("index2.html", show_profile=True, email=session['email'])
    else:
        # User is not logged in, show login link
        return render_template("index2.html", show_login=True)






@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user has entered information in the login form
    if request.method == 'POST':
        email = request.form['email']  # Change 'username' to 'email'
        login_user = users_collection.find_one({'email': email})

        # If a matching email is found
        if login_user:
            # If password is correct
            if bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['password']):
                session['email'] = email  # Set the user's email in the session
                return redirect('/loggedin')

        flash('Invalid email/password. Please try again.', 'error')

    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user has entered information in the registration form
    if request.method == 'POST':
        existing_user = users_collection.find_one({'email': request.form['email']})  # Change 'username' to 'email'

        # If entered data is not found in the DB
        if existing_user is None:
            # Encrypting entered password
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            # Inserting given information into DB with email
            users_collection.insert_one({'email': request.form['email'], 'password': hashpass})

            return redirect('/login')

        return 'Email already exists'

    return render_template('register.html')





@app.route('/loggedin')
def user():
    # If user is logged in (in session)
    if 'email' in session:
        # Simulate a slow redirect using time.sleep
        time.sleep(2)
        return redirect(url_for('profile_home', email=session['email']))

    flash('You are not logged in.')
    return redirect(url_for('login'))  # Use the endpoint name 'login' instead of the URL rule '/login'





@app.route('/profile_home/<email>', endpoint='profile_home')
def profile_home(email):
    if 'email' in session and session['email'] == email:
        return render_template('index2.html', show_profile=True, email=email)
    else:
        flash('Invalid access to profile.')
        return redirect(url_for('login'))
    







@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Remove current session
    session.pop('email', None)
    return redirect('/')





#Page for searching flights; source, destination and date fields
@app.route('/flight_search', methods=('GET', 'POST'))
def flight_search():
    # Fetch available cities from MongoDB
    available_cities = cities_collection.distinct("origin")

    if request.method == 'POST':
        from_city = request.form['from']
        to_city = request.form['to']
        date_ = request.form['departure_date']

        if from_city == to_city:
            flash('Source and destination cities cannot be the same. Please choose different cities.')
        else:
            # Store data in session variables
            session['from_city'] = from_city
            session['to_city'] = to_city
            session['date_of_flight'] = date_  # Updated key to match the form
            return redirect(url_for('results'))

    return render_template('flight_search.html', list_of_cities=available_cities)











@app.route('/results')
def results():
    # Retrieve data from session variable
    from_city = session.get('from_city', '')
    to_city = session.get('to_city', '')
    date_ = session.get('date_of_flight', '')

    # function to convert date to day of week format
    date_object = datetime.strptime(date_, '%Y-%m-%d')
    dayofweek = date_object.strftime("%A")

    # Data retrieval command to fetch specific source, destination, and date-wise records from MongoDB
    wanted_cities = cities_collection.find(
        {"origin": from_city, "destination": to_city, "daysOfWeek": {"$regex": dayofweek}},
        {
            "_id": 1,
            "airline": 1,
            "flightNumber": 1,
            "origin": 1,
            "destination": 1,
            "daysOfWeek": 1,
            "scheduledDepartureTime": 1,
            "scheduledArrivalTime": 1,
            "flightTime": 1,
            "rate": 1,
            "seatAvail": 1
        }
    )

    list_of_results = list(wanted_cities)
    flag = bool(list_of_results)  # Simplify the flag assignment

    # Check if user is logged in using email
    if 'email' in session:
        return render_template('results11.html', list_of_results=list_of_results, from_city=from_city, to_city=to_city,
                               flag=flag, dateoftrip=date_, dayofweek=dayofweek)
    else:
        # User is not logged in, redirect to login page
        flash('Please log in to proceed.')
        return redirect(url_for('login'))













@app.route('/book_flight', methods=['POST'])
def book_flight():
    # Check if user is logged in
    if 'email' in session:
        obj_id = request.form.get('obj_id')
        obj_id = ObjectId(obj_id)

        date_ = session.get('date_of_flight', '')
            
        # Find the document with the specified _id
        book_flight_record = cities_collection.find_one({'_id': obj_id})

        # Check if the document is found
        if book_flight_record:
            return render_template('book_flight.html', book_flight_record=book_flight_record, date_=date_)
        else:
            flash('Flight not found.')  # Add a flash message if the flight is not found
            return redirect(url_for('search_flight'))
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('login'))



@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    if request.method == 'POST':


        user_email = session.get('email', '')
        date_ = session.get('date_of_flight', '')
        # Retrieve passenger information from the form submission
        name = request.form.get('name')
        age = request.form.get('age')
        aadhaar = request.form.get('aadhaar')
        address = request.form.get('address')
        flight_id = request.form.get('flight_id')

        # Retrieve flight details from the database using the flight_id
        book_flight_record = cities_collection.find_one({'_id': ObjectId(flight_id)})

        # Generate a unique PNR ID
        pnr_id = secrets.token_urlsafe(8)  # You can adjust the length of the PNR ID

        # Create a dictionary with booking details, including the PNR ID
        booking_dict = {
            'pnr_id': pnr_id,
            'flight_id': ObjectId(flight_id),
            'flight_details': {
                'flightNumber': book_flight_record['flightNumber'],
                'origin': book_flight_record['origin'],
                'destination': book_flight_record['destination']
            },
            'passenger_details': {
                'name': name,
                'age': age,
                'aadhaar': aadhaar,
                'address': address,
                'email': user_email  # Add the user's email to the passenger details
            },
            'journey_date': date_
        }

        # Insert the dictionary into the passenger collection
        passenger_collection.insert_one(booking_dict)

        # Flash a success message with the PNR ID
        flash(f'Booking confirmed! Your PNR ID is {pnr_id}. Flight details are available under "My Bookings".')

        # Redirect to the home page or wherever you want
        return redirect(url_for('index'))

    return redirect(url_for('search_flight'))






#Alpha function to test pagination of the result from the MongoDB database
# -- NOT COMPLETE--


def get_user_bookings(email):
    email = session.get('email', '')
    # Add your logic to fetch user bookings from MongoDB or any relevant data source
    # user_bookings = passenger_collection.find({'email': email})
    user_bookings = passenger_collection.find({"passenger_details.email":session.get('email','')})

    # Convert the MongoDB cursor to a list for easier rendering in the template
    list_of_bookings = list(user_bookings)

    return list_of_bookings

@app.route('/my_bookings', endpoint='my_bookings')
def my_bookings():
    # Add your logic to fetch user bookings or any relevant data
    list_of_bookings = get_user_bookings(session.get('email', ''))
    print()

    return render_template('my_bookings.html', list_of_bookings=list_of_bookings)










@app.route("/get_pnr", methods=['GET'])
def get_pnr():
    return render_template('get_pnr.html')

@app.route("/get_pnr_details", methods=['POST'])
def get_pnr_details():
    pnr_id = request.form['pnr_id']

    # Assuming passenger_collection is your MongoDB collection object
    data = passenger_collection.find({"pnr_id": pnr_id})

    if data:
        pnr_data = {
            'pnr_id': data[0]['pnr_id'],
            'flight_number': data[0]['flight_details']['flightNumber'],
            'origin': data[0]['flight_details']['origin'],
            'destination': data[0]['flight_details']['destination'],
            'journey_date': data[0]['journey_date']
        }
        return render_template('get_pnr.html', pnr_data=pnr_data)
    else:
        return "PNR not found"  # You can return an error message or handle it as per your application logic

if __name__ == '__main__':
    app.run(debug=True)






if __name__ == "__main__":
    app.run(debug=True)
