import hashlib
from datetime import datetime
import re

def analyze_string(input_string):
    # Calculate properties
    length = len(input_string)
    
    # Case-insensitive palindrome check
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', input_string.lower())
    is_palindrome = cleaned == cleaned[::-1]
    
    # Unique characters
    unique_characters = len(set(input_string))
    
    # Word count
    word_count = len(input_string.split())
    
    # SHA256 hash
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()
    
    # Character frequency
    character_frequency_map = {}
    for char in input_string:
        character_frequency_map[char] = character_frequency_map.get(char, 0) + 1
    
    return {
        "id": sha256_hash,
        "value": input_string,
        "properties": {
            "length": length,
            "is_palindrome": is_palindrome,
            "unique_characters": unique_characters,
            "word_count": word_count,
            "sha256_hash": sha256_hash,
            "character_frequency_map": character_frequency_map
        },
        "created_at": datetime.utcnow().isoformat() + 'Z'
    }