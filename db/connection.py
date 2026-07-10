from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
import logging

log = logging.getLogger(__name__)

_client = None
_db = None

def get_db():
    # Returns the database instance, opening the connection on first call.
    global _client, _db

    if _db is not None:
        return _db

    mongo_uri = os.environ.get("DB_CONNECTION_STRING") or os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("DB_CONNECTION_STRING environment variable is not set.")

    try:
        _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client.get_default_database()
        log.info("MongoDB connected: %s", _client.host)
    except ConnectionFailure as e:
        log.error("MongoDB connection failed: %s", e)
        raise

    return _db
