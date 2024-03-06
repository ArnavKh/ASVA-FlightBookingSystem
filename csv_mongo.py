import csv
from pymongo import MongoClient

#connect to MongoDB

client = MongoClient("mongodb://localhost:27017/")
# replace with your db name
db = client["Flight_Booking_System"]
# relace with your collection name
collection = db["flights"]

# Open the CSv file

with open("flight_schedule_fixed_rates.csv","r") as csvfile:
    reader = csv.DictReader(csvfile)
    
    #Inser each row to the document
    for row in reader:
        collection.insert_one(row)

# Close the connection
client.close()