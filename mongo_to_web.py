from flask import Flask, render_template, request, flash, redirect, url_for, session
from pymongo import MongoClient
from pymongo import ASCENDING, DESCENDING
from bson.objectid import ObjectId
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import bcrypt
import time
import secrets
import re
import random
import string
import io
import base64
import json
import jsonify
import plotly
import plotly.express as px
import plotly.io as pio
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


nltk.data.path.append("/path/to/nltk_data")



app = Flask(__name__)
app.config['SECRET_KEY'] = '@\x9d1$\xff\x87\xddTb\x8elg'    

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Flight_Booking_System'] 
cities_collection = db['flights1']


client = MongoClient('mongodb://localhost:27017/')
db = client['Flight_Booking_System']
users_collection = db['User_Data']


passenger_client = MongoClient('mongodb://localhost:27017/')
passenger_db = passenger_client['Flight_Booking_System']
passenger_collection = passenger_db['Passenger_Data']




# Home page
@app.route("/")
def index():
    # Fetch available cities from MongoDB
    available_cities = cities_collection.distinct("origin")

    # Check if user is logged in
    if 'email' in session:
        # User is logged in, show profile option
        return render_template("flight_search.html", show_profile=True, email=session['email'], list_of_cities=available_cities)
    else:
        # User is not logged in, show login link
        return render_template("flight_search.html", show_login=True, list_of_cities=available_cities)
    
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

    
    # If it's a GET request or if there's a validation error in POST, render the template
    if 'email' in session:
        return render_template("flight_search.html", show_profile=True, email=session['email'], list_of_cities=available_cities)
    else:
        return render_template("flight_search.html", show_login=True, list_of_cities=available_cities)



nltk.download('punkt')   #For tokenization
nltk.download('stopwords')  #For removing the commonly used term(like 'and','is','was','they',etc.)

# Path to the data file
data=pd.read_csv("Flight_Booking_System.flights.csv")

def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text)
    sample = tokens
    tokens = [word.lower() for word in tokens if word.isalpha() and word not in stop_words]
    if "from" in sample:
        tokens.append('from')
    if "to" in sample:
        tokens.append('to')
    if "where" in sample:
        tokens.append('where')
    if "which" in sample:
        tokens.append('which')
    if "how" in sample:
        tokens.append('how')
    if "time" in sample:
        tokens.append("time")
    if "long" in sample:
        tokens.append("long")
    return tokens

def check_flight_id(flight_id, data):
    return flight_id in data['_id'].values

def handle_specific_query(flight_id, query, data):
    tokens = preprocess_text(query)
    flight_info = data[data['_id'] == flight_id].iloc[0]
    if any(word in tokens for word in ['airline', 'which airline', 'airlines', 'which airlines']):
        return f"The airline is {flight_info['airline']}."
    elif any(word in tokens for word in ['flight no', 'flight number', 'number']):
        return f"The flight number is {flight_info['flightNumber']}."
    elif any(word in tokens for word in ['source', 'depart', 'departing', 'from', 'coming', 'heading from', 'origin']):
        return f"The flight origin is {flight_info['origin']}."
    elif any(word in tokens for word in ['destination', 'landing', 'arrive', 'land', 'arrival', 'going', 'to', 'arriving']):
        return f"The flight destination is {flight_info['destination']}."
    elif any(word in tokens for word in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        found_day = None
        for day in days_of_week:
            if day in tokens:
                found_day = day
                break
        if found_day is not None:
            if flight_info[found_day.capitalize()] == 'Y':
                return f"Yes, this flight flies on {found_day.capitalize()}."
            else:
                return f"No, this flight doesn't fly on {found_day.capitalize()}."
        else:
            return "Day of the week not recognized in query."
    elif any(word in tokens for word in ['weekend', 'weekends']):
        if flight_info['Saturday'] == 'Y' or flight_info['Sunday'] == 'Y':
            return "Yes, this flight flies on the weekends."
        else:
            return "No, this flight doesn't fly on the weekends."
    elif any(word in tokens for word in ['weekday', 'weekdays']):
        if flight_info['Monday'] == 'Y' or flight_info['Tuesday'] == 'Y' or flight_info['Wednesday'] == 'Y' or flight_info['Thursday'] == 'Y' or flight_info['Friday'] == 'N':
            return "Yes, this flight flies on the weekdays."
        else:
            return "No, this flight doesn't fly on the weekdays."
    elif any(word in tokens for word in ['scheduledDepartureTime', 'departure']):
        return f"The scheduled departure time is {flight_info['scheduledDepartureTime']}."
    elif any(word in tokens for word in ['scheduledArrivalTime', 'arrival']):
        return f"The scheduled arrival time is {flight_info['scheduledArrivalTime']}."
    elif any(word in tokens for word in ['flighttime', 'time', 'long', 'duration']):
        if 'long' in tokens or 'time' or 'duration' in tokens:
            return f"The flight time in hours is {flight_info['flightTime']}."
        else:
            return "You can ask about the airline, flight number, origin, destination, operation days, scheduled times, flight time, rate, or seat availability."
    elif any(word in tokens for word in ['rate', 'price']):
        return f"The rate/price of the flight is {flight_info['rate']}."
    elif any(word in tokens for word in ['seats', 'available', 'avail']):
        return f"There are {flight_info['seatAvail']} seats available."
    else:
        return "You can ask about the airline, flight number, origin, destination, operation days, scheduled times, flight time, rate, or seat availability."

# List to store conversation history
conversation_history = []
flight_id_asked = False





# Route for displaying the login form with CAPTCHA
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user has entered information in the login form
    if request.method == 'POST':
        email = request.form['email']  # Change 'username' to 'email'
        login_user = users_collection.find_one({'email': email})

        # Get the form data including the CAPTCHA input
        captcha_input = request.form['captcha_input']
        
        # Get the CAPTCHA stored in the session
        captcha_session = session.get('captcha', '')

        # If a matching email is found
        if login_user:
            # Check if the input matches the CAPTCHA stored in the session
            if captcha_input.upper() != captcha_session:
                return 'CAPTCHA Incorrect! Please try again.'

            # If password is correct and CAPTCHA is valid
            if (bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['password'])) and (captcha_input.upper() == captcha_session):
                session['email'] = email  # Set the user's email in the session
                return redirect('/loggedin')
            

    # Generate a new CAPTCHA string and store it in the session
    captcha_string = generate_captcha()
    session['captcha'] = captcha_string

    # Render the login form with CAPTCHA
    return render_template('login.html', captcha=captcha_string)



# Route for displaying the registration form with CAPTCHA
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the form data
        email = request.form['email']
        password = request.form['password']
        captcha_input = request.form['captcha_input']
        
        # Get the CAPTCHA stored in the session
        captcha_session = session.get('captcha', '')
        
        # Check if the input matches the CAPTCHA stored in the session
        if captcha_input.upper() != captcha_session:
            return 'CAPTCHA Incorrect! Please try again.'
        
        # Check if the email already exists in the database
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return 'Email already exists'
        
        # Password validation using regular expression
        if not re.match(r"^(?=.*[A-Z])(?=.*[!@#$%^&*()_+}{:;'?/>.<,])(?=.*[a-z]).{5,}$", password):
            return 'Password must contain at least 1 symbol, 1 capital letter, and be at least 5 characters long.'
        
        # Encrypting entered password
        hashpass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Inserting given information into DB with email
        users_collection.insert_one({'email': email, 'password': hashpass})
        
        return redirect('/login')
    
    else:
        # Generate a new CAPTCHA string and store it in the session
        captcha_string = generate_captcha()
        session['captcha'] = captcha_string
        
        # Render the registration form with CAPTCHA
        return render_template('register.html', captcha=captcha_string)


# Generate a random CAPTCHA string
def generate_captcha():
    captcha_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return captcha_string



@app.route('/loggedin')
def user():
    # If user is logged in (in session)
    if 'email' in session:
        # Simulate a slow redirect using time.sleep
        time.sleep(2)
        return redirect(url_for('flight_search', email=session['email']))

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

    # Check if sorting by price is requested
    sort_by = request.args.get('sort')
    if sort_by == 'price_asc':
        wanted_cities.sort("rate", ASCENDING)
    elif sort_by == 'price_desc':
        wanted_cities.sort("rate", DESCENDING)
    elif sort_by == 'duration_asc':
        wanted_cities.sort("flightTime", ASCENDING)
    elif sort_by == 'duration_desc':
        wanted_cities.sort("flightTime", DESCENDING)
    elif sort_by == 'departure':
        wanted_cities.sort("scheduledDepartureTime", ASCENDING)

    list_of_results = list(wanted_cities)
    flag = bool(list_of_results)  # Simplify the flag assignment

    # Check if user is logged in using email
    # if 'email' in session:
    return render_template('results11.html', list_of_results=list_of_results, from_city=from_city, to_city=to_city,
                           flag=flag, dateoftrip=date_, dayofweek=dayofweek)
    # else:
    # User is not logged in, redirect to login page
    # flash('Please log in to proceed.')
    # return redirect(url_for('login'))









#Surab Sebait
# Function to book a flight and update seat availability
def book_flights(flight_id, booking_date):
    cities_collection.update_one(
        {"_id": ObjectId(flight_id), "instances.{}".format(booking_date): {"$exists": False}},
        {"$set": {"instances.{}".format(booking_date): {"seatAvail": 180}}}
    )
    cities_collection.update_one(
        {"_id": ObjectId(flight_id), "instances.{}.seatAvail".format(booking_date): {"$exists": True}},
        {"$inc": {"instances.{}.seatAvail".format(booking_date): -1}}
    )

# Page for booking a flight
@app.route('/book_flight', methods=['POST'])
def book_flight():
    # Check if user is logged in
    if 'email' in session:
        obj_id = request.form.get('obj_id')
        obj_id = ObjectId(obj_id)

        # Retrieve the date of flight from the session
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





# Page for flight booking confirmation
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

        # Validate age
        try:
            age = int(age)
            if not 0 <= age <= 100:
                raise ValueError("Age must be between 0 and 100.")
        except ValueError:
            error_message = "Age must be a valid integer between 0 and 100."
            return render_template('confirm_booking.html', error_message=error_message)

        # Check Aadhaar ID format using regex
        if not re.match(r'^\d{12}$', aadhaar):
            error_message = 'Aadhaar ID must be exactly 12 digits.'
            return render_template('confirm_booking.html', error_message=error_message)

        # Retrieve flight details from the database using the flight_id
        book_flight_record = cities_collection.find_one({'_id': ObjectId(flight_id)})

        # Check if flight record exists
        if not book_flight_record:
            error_message = 'Flight not found.'
            return render_template('confirm_booking.html', error_message=error_message)

        # Generate a unique PNR ID
        pnr_id = secrets.token_urlsafe(8)  # You can adjust the length of the PNR ID

        # Create a dictionary with booking details, including the PNR ID
        booking_dict = {
            'pnr_id': pnr_id,
            'flight_id': ObjectId(flight_id),
            'flight_details': {
                'flightNumber': book_flight_record['flightNumber'],
                'origin': book_flight_record['origin'],
                'destination': book_flight_record['destination'],
                'departure_time': book_flight_record['scheduledDepartureTime'],
                'arrival_time': book_flight_record['scheduledArrivalTime']
            },
            'passenger_details': {
                'name': name,
                'age': age,
                'aadhaar': aadhaar,
                'address': address,
                'email': user_email,  # Add the user's email to the passenger details
                'departure_time': book_flight_record['scheduledDepartureTime'],  # Include departure time in passenger details
                'arrival_time': book_flight_record['scheduledArrivalTime']  # Include arrival time in passenger details
            },
            'journey_date': date_
        }

        # Insert the dictionary into the passenger collection
        passenger_collection.insert_one(booking_dict)

        # Update seat availability in the cities collection
        book_flights(flight_id, date_)

        # Flash a success message with the PNR ID
        flash(f'Booking confirmed! Your PNR ID is {pnr_id}. Flight details are available under "My Bookings".')

        # Redirect to the home page or wherever you want
        return redirect(url_for('index'))

    return redirect(url_for('search_flight'))



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





# Route for canceling a flight using PNR number
@app.route('/cancel_flight', methods=['GET'])
def cancel_flight():
    return render_template('cancel_flight.html')

@app.route('/cancel_flight_user',methods=['POST'])
def cancel_flight_user():
    if request.method == 'POST':
        # Get the PNR number from the form submission
        pnr_id = request.form.get('pnr_id')

        # Find the booking associated with the provided PNR number
        booking = passenger_collection.find_one({'pnr_id': pnr_id})

        if booking:
            # Extract flight ID and journey date from the booking
            flight_id = booking['flight_id']
            journey_date = booking['journey_date']

            # Increment the seat availability in the cities collection for the specified flight and date
            cities_collection.update_one({'_id': ObjectId(flight_id), f'instances.{journey_date}.seatAvail': {'$exists': True}},
                                          {'$inc': {f'instances.{journey_date}.seatAvail': +1}})

            # Delete the booking from the passenger collection
            passenger_collection.delete_one({'pnr_id': pnr_id})

            flash('Flight canceled successfully!')
            return redirect(url_for('index'))
        else:
            flash('PNR number not found. Please check and try again.')
            return redirect(url_for('cancel_flight'))

    return redirect(url_for('index'))


# Get PNR details
@app.route("/get_pnr", methods=['GET'])
def get_pnr():
    return render_template('get_pnr.html', error_message=None)

@app.route("/get_pnr_details", methods=['POST'])
def get_pnr_details():
    pnr_id = request.form['pnr_id']

    # Retrieve PNR details from the database using the PNR ID
    data = passenger_collection.find_one({"pnr_id": pnr_id})

    if data:
        # Extract relevant details from the data
        pnr_data = {
            'pnr_id': data['pnr_id'],
            'flight_number': data['flight_details']['flightNumber'],
            'origin': data['flight_details']['origin'],
            'destination': data['flight_details']['destination'],
            'journey_date': data['journey_date'],
            'departure_time': data['flight_details'].get('departure_time', 'N/A'),
            'arrival_time': data['flight_details'].get('arrival_time', 'N/A')
        }
        return render_template('get_pnr.html', pnr_data=pnr_data, error_message=None)
    else:
        error_message = "PNR not found"
        return render_template('get_pnr.html', error_message=error_message)




@app.route("/data_analysis",methods=['GET'])
def data_analysis():
    return render_template('data_analysis.html')




cursor = cities_collection.find()
df = pd.DataFrame(list(cursor))



@app.route('/pie_chart')
def pie_with_plotly():
    # Check if DataFrame is empty
    if df.empty:
        return "No data available."
    
    # Process DataFrame to generate Pie chart
    airline_name = df['airline']
    airline_counter = Counter(airline_name)
    sorted_airline_counter = airline_counter.most_common()
    kys = [z[0] for z in sorted_airline_counter]
    vls = [x[1] for x in sorted_airline_counter]
    pie_keys = kys[:7]
    pie_values = vls[:7]
    x = sum(vls[8:])
    pie_values.append(x)
    pie_keys.append('Other')
    
    # Create Pie chart
    fig = go.Figure(data=[go.Pie(labels=pie_keys, values=pie_values, hole=.3)])
    fig.update_layout(width=800, height=800)  # Set width and height as desired
    
    # Convert figure to JSON
    graphJSON = fig.to_json()
    
    # Use render_template to pass graphJSON to html
    return render_template('pie_plot.html', graphJSON=graphJSON)


def plot_departure_time_slots(df, city):
    # Step 1: Filter the DataFrame to include only flights departing from the user-defined city
    city_flights = df[df['origin'] == city]
    
    # Step 2: Convert departure time to datetime object
    city_flights['scheduledDepartureTime'] = pd.to_datetime(city_flights['scheduledDepartureTime'])
    
    # Step 3: Create time slots
    slots = {
        'Before 6 AM': city_flights[(city_flights['scheduledDepartureTime'].dt.hour < 6)],
        '6 AM to 12 PM': city_flights[(city_flights['scheduledDepartureTime'].dt.hour >= 6) & (city_flights['scheduledDepartureTime'].dt.hour < 12)],
        '12 PM to 6 PM': city_flights[(city_flights['scheduledDepartureTime'].dt.hour >= 12) & (city_flights['scheduledDepartureTime'].dt.hour < 18)],
        'After 6 PM': city_flights[(city_flights['scheduledDepartureTime'].dt.hour >= 18)]
    }
    
    # Step 4: Count the number of flights in each time slot
    counts = [len(slot) for slot in slots.values()]
    
    # Step 5: Plot the counts of flights in each time slot
    fig = px.bar(x=list(slots.keys()), y=counts, labels={'x': 'Departure Time Slots', 'y': 'Number of Flights'}, 
                 color=['skyblue', 'lightgreen', 'lightcoral', 'lightsalmon'], title=f'Departure Time Slots for Flights from {city}')
    
    # Convert figure to JSON
    graphJSON = pio.to_json(fig)
    
    return graphJSON



@app.route('/city_selection', methods=['GET', 'POST'])
def city_selection():
    if request.method == 'POST':
        available_cities = cities_collection.distinct("origin")

        selected_city = request.form['city']
        # Process the selected city, you can perform further actions here
  
        graphJSON = plot_departure_time_slots(df, selected_city)
        # Use render_template to pass graphJSON to html
        return render_template('bar1_plot.html', graphJSON=graphJSON)
    else:
        available_cities = cities_collection.distinct("origin")
        return render_template('city_selection.html', avail_cities=available_cities)







@app.route('/flight_time_distribution')
def flight_time_distribution():
    # Check if DataFrame is empty
    if df.empty:
        return "No data available."
    
    # Process DataFrame to generate Bar chart
    flight_time_minutes = df['flightTimeMinutes']
    flight_time_minutes = pd.to_numeric(flight_time_minutes, errors='coerce')

    duration_ranges = {
        'Less than 1 hour': (0, 60),
        '1-2 hours': (60, 120),
        '2-4 hours': (120, 240),
        '4-8 hours': (240, 480),
        'More than 8 hours': (480, float('inf'))
    }

    flight_counts = {range_label: 0 for range_label in duration_ranges}

    for duration in flight_time_minutes:
        for range_label, (lower, upper) in duration_ranges.items():
            if lower <= duration < upper:
                flight_counts[range_label] += 1
                break

    time_ranges = list(flight_counts.keys())
    counts = list(flight_counts.values())

    # Create Bar chart

    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightsalmon', 'lightseagreen']

    fig = px.bar(x=time_ranges, y=counts, labels={'x': 'Time Range', 'y': 'Count'}, color=colors,title='Flight Time Distribution')
    
    # Convert figure to JSON
    graphJSON = pio.to_json(fig)
    
    # Use render_template to pass graphJSON to html
    return render_template('bar2_plot.html', graphJSON=graphJSON)




@app.route('/mean_airfare_distribution')
def airline_distribution():
    df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
    average_rate = df.groupby('airline')['rate'].mean().reset_index()

    average_rate_sorted = average_rate.sort_values(by='rate', ascending=True)

    average_rate_sorted['rate'] = average_rate_sorted['rate'].astype(int)

    fig = px.bar(x=average_rate_sorted['airline'], y=average_rate_sorted['rate'], orientation='v', 
                 color=average_rate_sorted['rate'])

    # Convert figure to JSON
    graphJSON = pio.to_json(fig)

    # Use render_template to pass graphJSON to html
    return render_template('bar3_plot.html', graphJSON=graphJSON)

@app.route('/chatbot1', methods=['GET'])
def chatbot1():
    global conversation_history
    conversation_history.append({'system': "Please enter the flight ID you're interested in:"})
    return render_template('chatbot1.html', conversation=conversation_history)
    


@app.route('/chat', methods=['POST'])
def chat():
    global conversation_history
    global flight_id_asked
    global verified_flight_id

    # Get user input from the form
    user_input = request.form['user_input']
    
    if not flight_id_asked:
        # Check if flight ID is valid
        if check_flight_id(user_input, data):
            verified_flight_id = user_input  # Store the verified flight ID
            conversation_history.append({'user': user_input})
            conversation_history.append({'system': "Flight ID recognized. You can now ask specific questions about this flight."})
            flight_id_asked = True
            conversation_history.append({'system': "Ask me about the source, destination, flight minutes, rate, or days of operation (or type 'quit' to exit): "})
        else:
            conversation_history.append({'user': user_input})
            conversation_history.append({'system': "Invalid flight ID. Please enter a valid flight ID."})
        return render_template('chatbot1.html', conversation=conversation_history)
    else:
        if user_input.lower() == 'quit':
            conversation_history.append({'user': user_input})
            conversation_history.append({'system': "Chat ended. Goodbye!"})
            return render_template('chatbot1.html', conversation=conversation_history)
        
        # Handle specific queries about the flight
        user_query = user_input
        if not check_flight_id(verified_flight_id, data):  # Check if the verified flight ID still exists in the data
            conversation_history.append({'user': user_query})
            conversation_history.append({'system': "Invalid flight ID. Please enter a valid flight ID."})
            return render_template('chatbot1.html', conversation=conversation_history)
        response = handle_specific_query(verified_flight_id, user_query, data)
        conversation_history.append({'user': user_query})
        conversation_history.append({'system': response})
        return render_template('chatbot1.html', conversation=conversation_history)



if __name__ == '__main__':
    app.run(debug=False, port=5600)