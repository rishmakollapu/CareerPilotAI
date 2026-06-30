from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))

db = client["CareerPilotAI"]

accounts = db["accounts"]
users = db["users"]
analysis = db["analysis"]
feedback = db["feedback"]