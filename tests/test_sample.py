"""Sample Python file with various code issues for testing."""

import os
import sys
import pickle

# Security issue: SQL injection
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

# Security issue: Command injection
def run_command(cmd):
    os.system(f"echo {cmd}")

# Performance issue: N+1 query
def get_all_users_with_posts():
    users = db.query("SELECT * FROM users")
    for user in users:
        posts = db.query(f"SELECT * FROM posts WHERE user_id = {user.id}")
        user.posts = posts
    return users

# Code quality: Unused import
import json

# Code quality: Mutable default argument
def add_item(item, items=[]):
    items.append(item)
    return items

# Code quality: Bare except
def risky_operation():
    try:
        dangerous_call()
    except:
        pass

# Complexity issue: High cyclomatic complexity
def complex_function(a, b, c, d):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    return "all positive"
                else:
                    return "d negative"
            else:
                return "c negative"
        else:
            return "b negative"
    else:
        return "a negative"

# Type issue: Inconsistent return types
def get_value(key):
    if key == "name":
        return "John"
    elif key == "age":
        return 30
    else:
        return None

# Resource leak
def read_file(filename):
    f = open(filename, 'r')
    data = f.read()
    return data  # File not closed

# String concatenation in loop
def build_string(items):
    result = ""
    for item in items:
        result = result + str(item) + ","
    return result

