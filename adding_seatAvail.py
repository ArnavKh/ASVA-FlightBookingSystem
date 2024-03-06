from pymongo import MongoClient

# Replace with your database and collection names
client = MongoClient("mongodb://localhost:27017/")
db = client["Flight_Booking_System"]
collection = db["flights"]

# Define the attribute name and value
attribute_name = "seatAvail"
attribute_value = 180

# Update all documents with the new attribute
result = collection.update_many({}, {"$set": {attribute_name: attribute_value}})
