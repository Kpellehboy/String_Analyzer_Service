import os
import re
import json
import hashlib
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# -----------------------------
# APP SETUP
# -----------------------------
app = Flask(__name__)
CORS(app)

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():
    """Initializes the SQLite database and table."""
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS strings (
            id TEXT PRIMARY KEY,
            value TEXT UNIQUE,
            data TEXT,
            created_at TEXT
        )''')
init_db()

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def analyze_string(value):
    """Analyze a string and compute properties."""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', value.lower())
    is_palindrome = cleaned == cleaned[::-1] if cleaned else True

    properties = {
        "length": len(value),
        "is_palindrome": is_palindrome,
        "unique_characters": len(set(value)),
        "word_count": len(value.split()),
        "sha256_hash": hashlib.sha256(value.encode()).hexdigest(),
        "character_frequency_map": {ch: value.count(ch) for ch in set(value)}
    }

    return {
        "id": properties["sha256_hash"],
        "value": value,
        "properties": properties,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

def row_to_obj(row):
    """Convert DB row to flattened JSON."""
    if not row:
        return None
    props = json.loads(row[2])
    return {
        "id": row[0],
        "value": row[1],
        "created_at": row[3],
        "length": props["length"],
        "is_palindrome": props["is_palindrome"],
        "unique_characters": props["unique_characters"],
        "word_count": props["word_count"],
        "sha256_hash": props["sha256_hash"],
        "character_frequency_map": props.get("character_frequency_map", {})
    }

# -----------------------------
# 1️⃣ POST /strings
# -----------------------------
@app.route("/strings", methods=["POST"])
def create_string():
    try:
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "Missing 'value' field"}), 400

        value = data["value"]
        if not isinstance(value, str):
            return jsonify({"error": "'value' must be a string"}), 422

        result = analyze_string(value)

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM strings WHERE id=?", (result["id"],))
            if cursor.fetchone():
                return jsonify({"error": "String already exists"}), 409

            cursor.execute(
                "INSERT INTO strings (id, value, data, created_at) VALUES (?, ?, ?, ?)",
                (result["id"], value, json.dumps(result["properties"]), result["created_at"])
            )
            conn.commit()

        return jsonify(result), 201

    except Exception as e:
        print("Error in create_string:", e)
        return jsonify({"error": "Internal server error"}), 500

# -----------------------------
# 2️⃣ GET /strings/<string_value>
# -----------------------------
@app.route("/strings/<path:string_value>", methods=["GET"])
def get_string(string_value):
    try:
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM strings WHERE value=?", (string_value,))
            row = cursor.fetchone()

        if not row:
            return jsonify({"error": "String not found"}), 404

        return jsonify(row_to_obj(row)), 200

    except Exception as e:
        print("Error in get_string:", e)
        return jsonify({"error": "Internal server error"}), 500

# -----------------------------
# 3️⃣ GET /strings (with filters)
# -----------------------------
@app.route("/strings", methods=["GET"])
def get_all_strings():
    try:
        params = request.args
        with sqlite3.connect("database.db") as conn:
            rows = conn.execute("SELECT * FROM strings").fetchall()

        data = [row_to_obj(r) for r in rows]
        filtered = []

        for d in data:
            match = True

            if "is_palindrome" in params:
                match &= d["is_palindrome"] == (params["is_palindrome"].lower() == "true")
            if "min_length" in params:
                match &= d["length"] >= int(params["min_length"])
            if "max_length" in params:
                match &= d["length"] <= int(params["max_length"])
            if "word_count" in params:
                match &= d["word_count"] == int(params["word_count"])
            if "contains_character" in params:
                match &= params["contains_character"].lower() in d["value"].lower()

            if match:
                filtered.append(d)

        return jsonify({"data": filtered, "count": len(filtered)}), 200

    except Exception as e:
        print("Error in get_all_strings:", e)
        return jsonify({"error": "Internal server error"}), 500

# -----------------------------
# 4️⃣ GET /strings/filter-by-natural-language
# -----------------------------
@app.route("/strings/filter-by-natural-language", methods=["GET"])
def filter_by_natural_language():
    try:
        query = request.args.get("query", "").lower().strip()
        if not query:
            return jsonify({"error": "Missing query parameter"}), 400

        filters = {}
        if "palindromic" in query or "palindrome" in query:
            filters["is_palindrome"] = True
        if "single word" in query:
            filters["word_count"] = 1

        if m := re.search(r"longer than (\d+)", query):
            filters["min_length"] = int(m.group(1)) + 1
        if m := re.search(r"shorter than (\d+)", query):
            filters["max_length"] = int(m.group(1)) - 1
        if m := re.search(r"containing (?:the letter )?(\w)", query):
            filters["contains_character"] = m.group(1)

        if not filters:
            return jsonify({"error": "Unable to parse natural language query"}), 400

        if "min_length" in filters and "max_length" in filters and filters["min_length"] > filters["max_length"]:
            return jsonify({"error": "Conflicting filters"}), 422

        with sqlite3.connect("database.db") as conn:
            rows = conn.execute("SELECT * FROM strings").fetchall()
        data = [row_to_obj(r) for r in rows]
        filtered = []

        for d in data:
            match = True
            if filters.get("is_palindrome") and not d["is_palindrome"]:
                match = False
            if "word_count" in filters and d["word_count"] != filters["word_count"]:
                match = False
            if "min_length" in filters and d["length"] < filters["min_length"]:
                match = False
            if "max_length" in filters and d["length"] > filters["max_length"]:
                match = False
            if "contains_character" in filters and filters["contains_character"].lower() not in d["value"].lower():
                match = False
            if match:
                filtered.append(d)

        return jsonify({"data": filtered, "count": len(filtered), "parsed_filters": filters}), 200

    except Exception as e:
        print("Error in filter_by_natural_language:", e)
        return jsonify({"error": "Internal server error"}), 500

# -----------------------------
# 5️⃣ DELETE /strings/<string_value>
# -----------------------------
@app.route("/strings/<path:string_value>", methods=["DELETE"])
def delete_string(string_value):
    try:
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM strings WHERE value=?", (string_value,))
            deleted = cursor.rowcount
            conn.commit()

        if deleted == 0:
            return jsonify({"error": "String not found"}), 404

        return "", 204

    except Exception as e:
        print("Error in delete_string:", e)
        return jsonify({"error": "Internal server error"}), 500

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "String Analyzer API is running!"}), 200

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
