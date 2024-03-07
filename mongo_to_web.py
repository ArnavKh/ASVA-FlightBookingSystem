from flask import Flask, render_template, request, flash, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_paginate import Pagination
from datetime import datetime
import calendar, pandas as pd


app = Flask(__name__)
app.config['SECRET_KEY'] = '@\x9d1$\xff\x87\xddTb\x8elg'    

# Connect to MongoDB
client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['flight_records'] 
cities_collection = db['flight_seats']


#Home page
@app.route("/")
def index():
    return render_template("index2.html")




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
    date_ = session.get('date_of_flight','')


    #function to convert date to day of week fromat
    
    date_object = datetime.strptime(date_, '%Y-%m-%d')
    y, m, d = date_object.year, date_object.month, date_object.day
    dayofweek = date_object.strftime("%A")


    # Data retreival command to to fetch the sepcific source, destination and date wise records from MongoBD
    wanted_cities = cities_collection.find(
        {"origin":from_city, "destination": to_city,  "daysOfWeek": {"$regex": dayofweek}},
        {
            "_id":1,
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

    return render_template('results1.html', list_of_results=list_of_results, from_city=from_city, to_city=to_city, flag=flag, dateoftrip = date_, dayofweek = dayofweek)





@app.route('/book_flight', methods=['POST'])
def book_flight():
    obj_id = request.form.get('obj_id')

    obj_id = ObjectId(obj_id)

# Find the document with the specified _id
    book_flight_record = cities_collection.find_one({'_id': obj_id})
    book_flight_record = list(book_flight_record)

    print(book_flight_record)

    return render_template('book_flight.html',book_flight_record = book_flight_record)






#Alpha function to test pagination of the result from the MongoDB database
# -- NOT COMPLETE--

""" @app.route('/results', methods=['GET', 'POST'])
def results():
    # Retrieve data from session variable
    from_city = session.get('from_city', '')
    to_city = session.get('to_city', '')

    # Use the data as needed (e.g., query the database)
    # cities_collection.find({'origin': from_city, 'destination': to_city})

    wanted_cities = cities_collection.find({"origin": "Pune", "destination": "Delhi"},
                                           {
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

    cnt_of_result = list(wanted_cities)

    page = request.args.get('page', type=int, default=1)
    per_page = 5
    total_results = len(cnt_of_result)
    offset = (page - 1) * per_page
    results_to_show = cnt_of_result[offset: offset + per_page]

    pagination = Pagination(
        page=page,
        total=total_results,
        per_page=per_page,
        css_framework='bootstrap4'
    )

    return render_template('alternative_result_pagination.html', list_of_results=results_to_show,
                           from_city=from_city, to_city=to_city, pagination=pagination)
 """











if __name__ == "__main__":
    app.run(debug=True)
