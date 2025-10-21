import os
from flask import Flask, request, jsonify
import sqlite3
import json
import hashlib
from datetime import datetime
import re
from flask_cors import CORS

# -----------------------------
# APP SETUP
# -----------------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# -----------------------------
# STRING ANALYSIS FUNCTION
# -----------------------------
def analyze_string(input_string):
    """Analyzes a string and returns a dictionary of its properties."""
    length = len(input_string)
    
    # Case-insensitive palindrome check (letters and numbers only)
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', input_string.lower())
    is_palindrome = cleaned == cleaned[::-1] if cleaned else True
    
    unique_characters = len(set(input_string))
    word_count = len(input_string.split())
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()
    
    character_frequency_map = {}
    for char in input_string:
        character_frequency_map[char] = character_frequency_map.get(char, 0) + 1
    
    # This structure is used for internal storage (DB 'data' field)
    properties_data = {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": character_frequency_map
    }

    # This structure is used for initial POST response
    return {
        "id": sha256_hash,
        "value": input_string,
        "properties": properties_data,
        "created_at": datetime.utcnow().isoformat() + 'Z'
    }

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():
    """Initializes the SQLite database and the 'strings' table."""
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS strings (
            id TEXT PRIMARY KEY,
            value TEXT UNIQUE,
            data TEXT,
            created_at TEXT
        )''')

init_db()

# -----------------------------
# DATABASE HELPER FUNCTION (MODIFIED FOR FLATTENED OUTPUT)
# -----------------------------
def row_to_obj(row):
    """Converts a SQLite row into a single, FLATTENED JSON object for API response."""
    if not row:
        return None
        
    # row[2] is the JSON string containing all properties
    properties = json.loads(row[2]) 

    # Combine top-level fields (row[0], row[1], row[3]) with the computed properties (properties)
    # This FLATTENS the structure to match your requested clean output.
    output = {
        "id": row[0],
        "created_at": row[3],
        "value": row[1],

        # Flattened properties:
        "length": properties.get("length"),
        "is_palindrome": properties.get("is_palindrome"),
        "unique_characters": properties.get("unique_characters"),
        "word_count": properties.get("word_count"),
        "sha256_hash": properties.get("sha256_hash"),
        "character_frequency_map": properties.get("character_frequency_map", {})
    }
    
    return output

# -----------------------------
# 1️⃣ POST /strings — Analyze and Store String
# -----------------------------
@app.route('/strings', methods=['POST'])
def create_string():
    try:
        data = request.get_json()
        
        if not data or 'value' not in data:
            return jsonify({"error": "Missing 'value' field"}), 400
        
        if not isinstance(data['value'], str):
            return jsonify({"error": "'value' must be a string"}), 422

        result = analyze_string(data['value'])

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM strings WHERE id=?", (result['id'],))
            if cursor.fetchone():
                return jsonify({"error": "String already exists"}), 409

            # Store the computed properties JSON string in the 'data' column
            cursor.execute("INSERT INTO strings (id, value, data, created_at) VALUES (?, ?, ?, ?)",
                          (result['id'], result['value'], json.dumps(result['properties']), result['created_at']))
            conn.commit()
        
        # Return the original result structure (which includes 'properties' as requested earlier)
        return jsonify(result), 201
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error in create_string: {e}") 
        return jsonify({"error": str(e)}), 500

# -----------------------------
# 2️⃣ GET /strings/<string_value> — Get Specific String
# -----------------------------
@app.route('/strings/<path:string_value>', methods=['GET'])
def get_string(string_value):
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM strings WHERE value=?", (string_value,))
            row = cursor.fetchone()

        if not row:
            return jsonify({"error": "String not found"}), 404
        
        # Use the modified row_to_obj for a flattened response
        return jsonify(row_to_obj(row)), 200
    
    except Exception as e:
        print(f"Error in get_string: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# 3️⃣ GET /strings — Get All Strings with Filtering
# -----------------------------
@app.route('/strings', methods=['GET'])
def get_all_strings():
    try:
        query_params = request.args
        
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM strings")
            rows = cursor.fetchall()

        # The row_to_obj returns the FLATTENED structure, which must be used for filtering
        data = [row_to_obj(r) for r in rows]
        filtered = []

        is_palindrome = query_params.get('is_palindrome')
        min_length = query_params.get('min_length')
        max_length = query_params.get('max_length')
        word_count = query_params.get('word_count')
        contains_char = query_params.get('contains_character')

        for d in data:
            match = True
            
            # Apply filters
            if is_palindrome is not None:
                filter_bool = is_palindrome.lower() == 'true'
                # Access the flattened key directly: d["is_palindrome"]
                if d.get("is_palindrome") != filter_bool: 
                    match = False
            
            if match and min_length:
                try:
                    # Access the flattened key directly: d["length"]
                    if d.get("length") < int(min_length):
                        match = False
                except (ValueError, TypeError):
                    pass # Ignore if min_length is not a valid number
            
            if match and max_length:
                try:
                    # Access the flattened key directly: d["length"]
                    if d.get("length") > int(max_length):
                        match = False
                except (ValueError, TypeError):
                    pass # Ignore if max_length is not a valid number
            
            if match and word_count:
                try:
                    # Access the flattened key directly: d["word_count"]
                    if d.get("word_count") != int(word_count):
                        match = False
                except (ValueError, TypeError):
                    pass # Ignore if word_count is not a valid number
            
            # d["value"] is already a top-level key in the flattened object
            if match and contains_char and contains_char not in d["value"]:
                match = False
            
            if match:
                filtered.append(d)

        return jsonify({
            "data": filtered,
            "count": len(filtered),
            "filters_applied": dict(query_params)
        }), 200
    
    except Exception as e:
        print(f"Error in get_all_strings: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# 4️⃣ GET /strings/filter-by-natural-language (Unchanged)
# -----------------------------
@app.route('/strings/filter-by-natural-language', methods=['GET'])
def natural_language_filter():
    try:
        query = request.args.get("query", "").lower().strip()
        filters = {}

        # --- Natural language parsing ---
        if "palindromic" in query or "palindrome" in query:
            filters["is_palindrome"] = True

        if "single word" in query:
            filters["word_count"] = 1

        # Matches 'longer than 5' -> min_length = 6
        match = re.search(r"longer than (\d+)", query)
        if match:
            filters["min_length"] = int(match.group(1)) + 1

        # Matches 'shorter than 10' -> max_length = 9
        match = re.search(r"shorter than (\d+)", query)
        if match:
            filters["max_length"] = int(match.group(1)) - 1

        match = re.search(r"containing the letter (\w)", query)
        if match:
            filters["contains_character"] = match.group(1)
        else:
            match = re.search(r"containing (\w)", query)
            if match:
                filters["contains_character"] = match.group(1)

        if not filters:
            return jsonify({"error": "Unable to parse natural language query"}), 400

        # --- Conflict handling ---
        if "min_length" in filters and "max_length" in filters and filters["min_length"] > filters["max_length"]:
            return jsonify({
                "error": "Query parsed but resulted in conflicting filters",
                "parsed_filters": filters
            }), 422

        # --- Apply filters ---
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM strings")
            rows = cursor.fetchall()

        # The row_to_obj returns the FLATTENED structure, which must be used for filtering
        data = [row_to_obj(r) for r in rows]
        filtered = []

        for d in data:
            # All checks now access the flattened keys directly (e.g., d["is_palindrome"])
            match_flag = True

            if filters.get("is_palindrome") and not d.get("is_palindrome"):
                match_flag = False
            if "word_count" in filters and d.get("word_count") != filters["word_count"]:
                match_flag = False
            if "min_length" in filters and d.get("length") < filters["min_length"]:
                match_flag = False
            if "max_length" in filters and d.get("length") > filters["max_length"]:
                match_flag = False
            if "contains_character" in filters and filters["contains_character"].lower() not in d["value"].lower():
                match_flag = False

            if match_flag:
                filtered.append(d)

        return jsonify({
            "data": filtered,
            "count": len(filtered),
            "interpreted_query": {
                "original": query,
                "parsed_filters": filters
            }
        }), 200

    except Exception as e:
        print(f"Error in natural_language_filter: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# 5️⃣ DELETE /strings/<string_value>
# -----------------------------
@app.route('/strings/<path:string_value>', methods=['DELETE'])
def delete_string(string_value):
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM strings WHERE value=?", (string_value,))
            deleted = cursor.rowcount
            conn.commit()

        if deleted == 0:
            return jsonify({"error": "String not found"}), 404
        
        return '', 204
    
    except Exception as e:
        print(f"Error in delete_string: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "String Analyzer API is running!"}), 200

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Note: Setting debug=True is often safer in a local environment for development
    app.run(host="0.0.0.0", port=port, debug=True)