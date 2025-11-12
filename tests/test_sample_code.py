"""Sample code with various issues for testing."""

import os
import sys

# Security issue: hardcoded password
PASSWORD = "admin123"

def unsafe_query(user_input):
    """SQL injection vulnerability."""
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query

def inefficient_loop():
    """Performance issue: string concatenation in loop."""
    result = ""
    for i in range(1000):
        result = result + str(i)
    return result

def missing_types(x, y):
    """Missing type hints."""
    return x + y

def bare_except():
    """Bad exception handling."""
    try:
        risky_operation()
    except:
        pass

def risky_operation():
    """Dummy function."""
    return 1 / 0

# Unused import
import json

class ComplexFunction:
    """High complexity function."""
    
    def complex_method(self, a, b, c, d):
        """Very complex logic."""
        if a > 0:
            if b > 0:
                if c > 0:
                    if d > 0:
                        return a + b + c + d
                    else:
                        return a + b + c
                else:
                    return a + b
            else:
                return a
        else:
            return 0

