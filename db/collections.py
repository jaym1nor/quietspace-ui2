from pymongo import ASCENDING, DESCENDING
from db.connection import get_db
import logging

log = logging.getLogger(__name__)

# Schema validators for each collection
STAFF_USERS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email", "password_hash", "role"],
        "properties": {
            "name":          {"bsonType": "string"},
            "email":         {"bsonType": "string"},
            "password_hash": {"bsonType": "string"},
            "role":          {"bsonType": "string", "enum": ["admin", "staff"]},
            "is_active":     {"bsonType": "bool"},
            "last_login":    {"bsonType": ["date", "null"]},
            "created_at":    {"bsonType": "date"},
        },
    }
}

ROOMS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "qr_token", "qr_url"],
        "properties": {
            "name":       {"bsonType": "string"},
            "location":   {"bsonType": "object"},
            "qr_token":   {"bsonType": "string"},
            "qr_url":     {"bsonType": "string"},
            "is_active":  {"bsonType": "bool"},
            "capacity":   {"bsonType": ["int", "null"]},
            "tags":       {"bsonType": "array"},
            "created_at": {"bsonType": "date"},
        },
    }
}

NOISE_REPORTS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["room_id", "room_name", "source", "reported_at"],
        "properties": {
            "room_id":       {"bsonType": "objectId"},
            "room_name":     {"bsonType": "string"},
            "source":        {"bsonType": "string", "enum": ["alert", "report"]},
            "reported_at":   {"bsonType": "date"},
            "status":        {"bsonType": ["string", "null"]},
            "noise_type":    {"bsonType": ["string", "null"]},
            "severity":      {"bsonType": ["string", "null"]},
            "details":       {"bsonType": ["string", "null"]},
            "other_details": {"bsonType": ["string", "null"]},
            "resolved":      {"bsonType": "bool"},
            "resolved_by":   {"bsonType": ["objectId", "null"]},
            "resolved_at":   {"bsonType": ["date", "null"]},
        },
    }
}


def init_collections():
    """Creates collections and indexes if they don't already exist. Called once at startup."""
    db = get_db()
    existing = db.list_collection_names()

    if "staff_users" not in existing:
        db.create_collection("staff_users", validator=STAFF_USERS_VALIDATOR)
        log.info("Created collection: staff_users")
    db.staff_users.create_index([("email", ASCENDING)], unique=True)

    if "rooms" not in existing:
        db.create_collection("rooms", validator=ROOMS_VALIDATOR)
        log.info("Created collection: rooms")
    db.rooms.create_index([("qr_token", ASCENDING)], unique=True)
    db.rooms.create_index([("name", ASCENDING)])

    if "noise_reports" not in existing:
        db.create_collection("noise_reports", validator=NOISE_REPORTS_VALIDATOR)
        log.info("Created collection: noise_reports")
    # Compound index for room + time range queries
    db.noise_reports.create_index([("room_id", ASCENDING), ("reported_at", DESCENDING)])
    db.noise_reports.create_index([("reported_at", DESCENDING)])
    db.noise_reports.create_index([("source", ASCENDING)])

    log.info("Collections and indexes ready.")


# Convenience accessors
def staff_users():
    return get_db().staff_users

def rooms():
    return get_db().rooms

def noise_reports():
    return get_db().noise_reports
