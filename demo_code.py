"""
Demo code with various issues for testing reviewr optimizations.
"""

import os
import pickle

# Security issue: SQL injection vulnerability
def get_user(username):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return execute_query(query)

# Security issue: Unsafe deserialization
def load_data(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# Performance issue: Inefficient loop
def process_items(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result

# Correctness issue: Potential division by zero
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

# Maintainability issue: Function too long
def complex_function(data):
    # This function does too many things
    result = []
    for item in data:
        if item > 0:
            if item % 2 == 0:
                result.append(item * 2)
            else:
                result.append(item * 3)
        else:
            if item < -10:
                result.append(item / 2)
            else:
                result.append(item - 1)
    
    # More processing
    final = []
    for r in result:
        if r > 100:
            final.append(r)
    
    return final

# Security issue: Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"

# Performance issue: Nested loops
def find_duplicates(list1, list2):
    duplicates = []
    for item1 in list1:
        for item2 in list2:
            if item1 == item2:
                duplicates.append(item1)
    return duplicates

# Correctness issue: Mutable default argument
def add_item(item, items=[]):
    items.append(item)
    return items

# Security issue: Path traversal vulnerability
def read_file(filename):
    path = "/var/data/" + filename
    with open(path, 'r') as f:
        return f.read()

