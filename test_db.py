from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("MONGO_URI")

print("URI:", uri)

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    print("✅ Connected successfully!")
except Exception as e:
    print("❌ Error:")
    print(e)