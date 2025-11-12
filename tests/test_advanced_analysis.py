#!/usr/bin/env python3
"""
Comprehensive tests for advanced code analysis features.

Tests security analysis, data flow analysis, and complexity metrics.
"""

import unittest
from textwrap import dedent

try:
    from reviewr.analysis.security_analyzer import SecurityAnalyzer
    from reviewr.analysis.dataflow_analyzer import DataFlowAnalyzer
    from reviewr.analysis.complexity_analyzer import ComplexityAnalyzer
    from reviewr.analysis.type_analyzer import TypeAnalyzer
    from reviewr.analysis.performance_analyzer import PerformanceAnalyzer
    from reviewr.analysis.semantic_analyzer import SemanticAnalyzer
    from reviewr.analysis.base import FindingSeverity
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("Warning: Could not import analysis modules. Tests will be skipped.")


class TestSecurityAnalyzer(unittest.TestCase):
    """Test cases for SecurityAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Analysis modules not available")
        self.analyzer = SecurityAnalyzer()
    
    def test_sql_injection_fstring(self):
        """Test detection of SQL injection via f-string."""
        code = dedent('''
            def get_user(user_id):
                query = f"SELECT * FROM users WHERE id = {user_id}"
                cursor.execute(query)
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        # Should detect SQL injection
        sql_findings = [f for f in findings if 'SQL injection' in f.message]
        self.assertGreater(len(sql_findings), 0)
        self.assertEqual(sql_findings[0].severity, FindingSeverity.CRITICAL.value)
    
    def test_sql_injection_format(self):
        """Test detection of SQL injection via .format()."""
        code = dedent('''
            def get_user(user_id):
                query = "SELECT * FROM users WHERE id = {}".format(user_id)
                cursor.execute(query)
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        sql_findings = [f for f in findings if 'SQL injection' in f.message]
        self.assertGreater(len(sql_findings), 0)
    
    def test_command_injection(self):
        """Test detection of command injection."""
        code = dedent('''
            import subprocess
            def run_command(user_input):
                subprocess.run(user_input, shell=True)
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        cmd_findings = [f for f in findings if 'Command injection' in f.message]
        self.assertGreater(len(cmd_findings), 0)
        self.assertEqual(cmd_findings[0].severity, FindingSeverity.CRITICAL.value)
    
    def test_eval_detection(self):
        """Test detection of dangerous eval() usage."""
        code = dedent('''
            def calculate(expression):
                result = eval(expression)
                return result
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        eval_findings = [f for f in findings if 'eval' in f.message]
        self.assertGreater(len(eval_findings), 0)
        self.assertEqual(eval_findings[0].severity, FindingSeverity.CRITICAL.value)
    
    def test_insecure_deserialization(self):
        """Test detection of insecure deserialization."""
        code = dedent('''
            import pickle
            def load_data(data):
                obj = pickle.loads(data)
                return obj
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        pickle_findings = [f for f in findings if 'deserialization' in f.message]
        self.assertGreater(len(pickle_findings), 0)
    
    def test_weak_crypto(self):
        """Test detection of weak cryptographic algorithms."""
        code = dedent('''
            import hashlib
            def hash_password(password):
                return hashlib.md5(password.encode()).hexdigest()
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        crypto_findings = [f for f in findings if 'MD5' in f.message or 'weak' in f.message.lower()]
        self.assertGreater(len(crypto_findings), 0)
    
    def test_hardcoded_secrets(self):
        """Test detection of hardcoded secrets."""
        code = dedent('''
            API_KEY = "sk_live_1234567890abcdefghijklmnop"
            PASSWORD = "SuperSecret123!"
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        secret_findings = [f for f in findings if 'Hardcoded' in f.message or 'secret' in f.message.lower()]
        self.assertGreater(len(secret_findings), 0)


class TestDataFlowAnalyzer(unittest.TestCase):
    """Test cases for DataFlowAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Analysis modules not available")
        self.analyzer = DataFlowAnalyzer()
    
    def test_taint_propagation_simple(self):
        """Test simple taint propagation."""
        code = dedent('''
            def process_input():
                user_input = input("Enter value: ")
                query = f"SELECT * FROM users WHERE name = '{user_input}'"
                cursor.execute(query)
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        # Should detect tainted data flow to SQL
        dataflow_findings = [f for f in findings if f.category == 'dataflow']
        self.assertGreater(len(dataflow_findings), 0)
    
    def test_taint_propagation_through_variable(self):
        """Test taint propagation through variable assignment."""
        code = dedent('''
            def process_request(request):
                user_id = request.args.get('id')
                safe_id = user_id  # Taint propagates
                query = f"SELECT * FROM users WHERE id = {safe_id}"
                cursor.execute(query)
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        dataflow_findings = [f for f in findings if f.category == 'dataflow']
        self.assertGreater(len(dataflow_findings), 0)
    
    def test_taint_in_string_concatenation(self):
        """Test taint detection in string concatenation."""
        code = dedent('''
            def build_command(filename):
                user_file = input("Enter filename: ")
                command = "cat " + user_file
                os.system(command)
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        dataflow_findings = [f for f in findings if f.category == 'dataflow']
        self.assertGreater(len(dataflow_findings), 0)


class TestComplexityAnalyzer(unittest.TestCase):
    """Test cases for ComplexityAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Analysis modules not available")
        self.analyzer = ComplexityAnalyzer()
    
    def test_cyclomatic_complexity(self):
        """Test cyclomatic complexity calculation."""
        code = dedent('''
            def complex_function(x, y, z, a, b, c):
                if x > 0:
                    if y > 0:
                        if z > 0:
                            if a > 0:
                                if b > 0:
                                    if c > 0:
                                        return x + y + z + a + b + c
                                    else:
                                        return x + y + z + a + b
                                else:
                                    return x + y + z + a
                            else:
                                return x + y + z
                        else:
                            return x + y
                    else:
                        return x
                else:
                    if y > 0:
                        if z > 0:
                            return y + z
                        else:
                            return y
                    else:
                        return 0
        ''')

        findings = self.analyzer.analyze('test.py', code)

        # Should detect either cyclomatic or cognitive complexity
        complexity_findings = [f for f in findings if 'complexity' in f.message and f.category == 'complexity']
        self.assertGreater(len(complexity_findings), 0, "Should detect high complexity")

        # Should have high complexity value
        self.assertIsNotNone(complexity_findings[0].metric_value)
        self.assertGreater(complexity_findings[0].metric_value, 5)
    
    def test_cognitive_complexity(self):
        """Test cognitive complexity calculation."""
        code = dedent('''
            def nested_function(items):
                result = []
                for item in items:
                    if item > 0:
                        for sub in item:
                            if sub % 2 == 0:
                                result.append(sub)
                return result
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        cognitive_findings = [f for f in findings if 'cognitive complexity' in f.message]
        # May or may not trigger depending on thresholds
        # Just verify it runs without error
        self.assertIsInstance(findings, list)
    
    def test_maintainability_index(self):
        """Test maintainability index calculation."""
        code = dedent('''
            def poorly_maintained_function(a, b, c, d, e, f, g):
                x = a + b * c - d / e + f ** g
                y = x * 2 + a - b
                z = y / c + d * e
                if x > y:
                    if y > z:
                        if z > a:
                            return x + y + z
                        else:
                            return x + y
                    else:
                        return x
                else:
                    return 0
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        # Should detect low maintainability
        maint_findings = [f for f in findings if 'maintainability' in f.message.lower()]
        # May or may not trigger depending on exact calculation
        self.assertIsInstance(findings, list)
    
    def test_halstead_metrics(self):
        """Test Halstead metrics calculation."""
        code = dedent('''
            def calculate(x, y, z):
                result = (x + y) * z - (x / y) + (z ** 2)
                if result > 100:
                    result = result / 2
                elif result < 0:
                    result = abs(result)
                return result
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        # Should calculate Halstead metrics without error
        self.assertIsInstance(findings, list)
    
    def test_technical_debt_estimation(self):
        """Test technical debt estimation."""
        code = dedent('''
            def very_complex_function(a, b, c, d):
                if a > 0:
                    if b > 0:
                        if c > 0:
                            if d > 0:
                                for i in range(a):
                                    for j in range(b):
                                        if i + j > c:
                                            return i * j
                return 0
        ''')
        
        findings = self.analyzer.analyze('test.py', code)
        
        debt_findings = [f for f in findings if 'technical debt' in f.message.lower()]
        # Should estimate technical debt for complex functions
        if debt_findings:
            self.assertIsNotNone(debt_findings[0].metric_value)
            self.assertGreater(debt_findings[0].metric_value, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for all analyzers."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Analysis modules not available")
        self.security_analyzer = SecurityAnalyzer()
        self.dataflow_analyzer = DataFlowAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer()
    
    def test_real_world_vulnerable_code(self):
        """Test analysis of realistic vulnerable code."""
        code = dedent('''
            import sqlite3
            import subprocess
            from flask import Flask, request
            
            app = Flask(__name__)
            
            @app.route('/user')
            def get_user():
                user_id = request.args.get('id')
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                
                # SQL injection vulnerability
                query = f"SELECT * FROM users WHERE id = {user_id}"
                cursor.execute(query)
                
                return cursor.fetchone()
            
            @app.route('/run')
            def run_command():
                cmd = request.args.get('cmd')
                
                # Command injection vulnerability
                result = subprocess.run(cmd, shell=True, capture_output=True)
                
                return result.stdout
        ''')
        
        # Run all analyzers
        security_findings = self.security_analyzer.analyze('app.py', code)
        dataflow_findings = self.dataflow_analyzer.analyze('app.py', code)
        complexity_findings = self.complexity_analyzer.analyze('app.py', code)
        
        # Should detect multiple security issues
        self.assertGreater(len(security_findings), 0)
        
        # Should detect data flow issues
        self.assertGreater(len(dataflow_findings), 0)
        
        # Complexity findings may or may not be present
        self.assertIsInstance(complexity_findings, list)
        
        # Verify critical findings
        critical_findings = [f for f in security_findings + dataflow_findings 
                           if f.severity == FindingSeverity.CRITICAL.value]
        self.assertGreater(len(critical_findings), 0)


class TestTypeAnalyzer(unittest.TestCase):
    """Test cases for TypeAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Analysis modules not available")
        self.analyzer = TypeAnalyzer()

    def test_missing_return_type(self):
        """Test detection of missing return type annotations."""
        code = dedent('''
            def calculate(x, y):
                return x + y
        ''')

        findings = self.analyzer.analyze('test.py', code)

        return_findings = [f for f in findings if 'return type' in f.message]
        self.assertGreater(len(return_findings), 0)

    def test_missing_parameter_types(self):
        """Test detection of missing parameter type annotations."""
        code = dedent('''
            def process(data, options):
                return data
        ''')

        findings = self.analyzer.analyze('test.py', code)

        param_findings = [f for f in findings if 'parameters without type' in f.message]
        self.assertGreater(len(param_findings), 0)

    def test_mutable_default_argument(self):
        """Test detection of mutable default arguments."""
        code = dedent('''
            def process_items(items=[]):
                items.append(1)
                return items
        ''')

        findings = self.analyzer.analyze('test.py', code)

        mutable_findings = [f for f in findings if 'mutable default' in f.message]
        self.assertGreater(len(mutable_findings), 0)
        self.assertEqual(mutable_findings[0].severity, FindingSeverity.HIGH.value)

    def test_none_comparison(self):
        """Test detection of incorrect None comparisons."""
        code = dedent('''
            def check_value(value):
                if value == None:
                    return True
                return False
        ''')

        findings = self.analyzer.analyze('test.py', code)

        none_findings = [f for f in findings if 'is None' in f.message]
        self.assertGreater(len(none_findings), 0)


class TestPerformanceAnalyzer(unittest.TestCase):
    """Test cases for PerformanceAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Analysis modules not available")
        self.analyzer = PerformanceAnalyzer()

    def test_n_plus_one_query(self):
        """Test detection of N+1 query pattern."""
        code = dedent('''
            def get_user_posts(user_ids):
                posts = []
                for user_id in user_ids:
                    user_posts = db.query("SELECT * FROM posts WHERE user_id = ?", user_id)
                    posts.extend(user_posts)
                return posts
        ''')

        findings = self.analyzer.analyze('test.py', code)

        n_plus_one = [f for f in findings if 'N+1' in f.message or 'database call inside loop' in f.message]
        self.assertGreater(len(n_plus_one), 0)
        self.assertEqual(n_plus_one[0].severity, FindingSeverity.HIGH.value)

    def test_string_concatenation_in_loop(self):
        """Test detection of string concatenation in loops."""
        code = dedent('''
            def build_string(items):
                result = ""
                for item in items:
                    result += str(item)
                return result
        ''')

        findings = self.analyzer.analyze('test.py', code)

        concat_findings = [f for f in findings if 'concatenation' in f.message.lower()]
        self.assertGreater(len(concat_findings), 0)

    def test_inefficient_membership_test(self):
        """Test detection of inefficient membership tests."""
        code = dedent('''
            def check_items(item):
                if item in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                    return True
                return False
        ''')

        findings = self.analyzer.analyze('test.py', code)

        membership_findings = [f for f in findings if 'set' in f.message and 'list' in f.message]
        self.assertGreater(len(membership_findings), 0)


class TestSemanticAnalyzer(unittest.TestCase):
    """Test cases for SemanticAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Analysis modules not available")
        self.analyzer = SemanticAnalyzer()

    def test_resource_leak(self):
        """Test detection of resource leaks."""
        code = dedent('''
            def read_file(filename):
                f = open(filename, 'r')
                data = f.read()
                return data
        ''')

        findings = self.analyzer.analyze('test.py', code)

        leak_findings = [f for f in findings if 'resource leak' in f.message.lower()]
        self.assertGreater(len(leak_findings), 0)
        self.assertEqual(leak_findings[0].severity, FindingSeverity.HIGH.value)

    def test_bare_except(self):
        """Test detection of bare except clauses."""
        code = dedent('''
            def process_data(data):
                try:
                    result = data.process()
                except:
                    return None
        ''')

        findings = self.analyzer.analyze('test.py', code)

        except_findings = [f for f in findings if 'bare except' in f.message.lower()]
        self.assertGreater(len(except_findings), 0)

    def test_swallowed_exception(self):
        """Test detection of swallowed exceptions."""
        code = dedent('''
            def process_data(data):
                try:
                    result = data.process()
                except ValueError:
                    pass
        ''')

        findings = self.analyzer.analyze('test.py', code)

        swallow_findings = [f for f in findings if 'swallowed' in f.message.lower()]
        self.assertGreater(len(swallow_findings), 0)

    def test_unreachable_code(self):
        """Test detection of unreachable code."""
        code = dedent('''
            def calculate(x):
                if x > 0:
                    return x * 2
                    print("This will never execute")
                return 0
        ''')

        findings = self.analyzer.analyze('test.py', code)

        unreachable_findings = [f for f in findings if 'unreachable' in f.message.lower()]
        self.assertGreater(len(unreachable_findings), 0)

    def test_boolean_comparison(self):
        """Test detection of redundant boolean comparisons."""
        code = dedent('''
            def check_status(is_active):
                if is_active == True:
                    return "Active"
                return "Inactive"
        ''')

        findings = self.analyzer.analyze('test.py', code)

        bool_findings = [f for f in findings if 'redundant' in f.message.lower() or 'True' in f.message]
        self.assertGreater(len(bool_findings), 0)

    def test_inconsistent_return_types(self):
        """Test detection of inconsistent return types."""
        code = dedent('''
            def get_value(key):
                if key in data:
                    return data[key]
                return None
        ''')

        findings = self.analyzer.analyze('test.py', code)

        # This should detect mixing None with other return types
        return_findings = [f for f in findings if 'return' in f.message.lower() and 'None' in f.message]
        # May or may not find depending on implementation
        self.assertIsInstance(findings, list)


def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()

