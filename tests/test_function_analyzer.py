import unittest
import ast

from repo_ingestor.function_analyzer import (
    FunctionInfo,
    PythonFunctionCallAnalyzer,
    build_call_graph_from_files,
    analyze_non_python_functions
)


class TestFunctionInfo(unittest.TestCase):

    def test_function_info_creation(self):
        # Create a FunctionInfo object
        func_info = FunctionInfo(
            name="test_function",
            file_path="test.py",
            start_line=10,
            end_line=20
        )

        # Verify attributes
        self.assertEqual(func_info.name, "test_function")
        self.assertEqual(func_info.file_path, "test.py")
        self.assertEqual(func_info.start_line, 10)
        self.assertEqual(func_info.end_line, 20)
        self.assertEqual(func_info.calls, [])
        self.assertEqual(func_info.called_by, [])

    def test_function_info_to_dict(self):
        # Create a FunctionInfo object
        func_info = FunctionInfo(
            name="test_function",
            file_path="test.py",
            start_line=10,
            end_line=20
        )

        # Add some calls and called_by
        func_info.calls = ["other_function", "another_function"]
        func_info.called_by = ["caller_function"]

        # Get the dictionary representation
        func_dict = func_info.to_dict()

        # Verify dictionary
        self.assertEqual(func_dict["name"], "test_function")
        self.assertEqual(func_dict["file_path"], "test.py")
        self.assertEqual(func_dict["start_line"], 10)
        self.assertEqual(func_dict["end_line"], 20)
        self.assertEqual(func_dict["calls"], ["other_function", "another_function"])
        self.assertEqual(func_dict["called_by"], ["caller_function"])


class TestPythonFunctionAnalyzer(unittest.TestCase):

    def test_python_analyzer(self):
        # Python code with functions
        python_code = """
def main():
    print("Hello")
    helper_function()
    return calculate_sum(1, 2)

def helper_function():
    print("Helper")

def calculate_sum(a, b):
    return a + b

class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""

        # Create an analyzer
        analyzer = PythonFunctionCallAnalyzer("test.py")
        tree = analyzer.visit(ast.parse(python_code))

        # Verify functions were found
        self.assertIn("main", analyzer.functions)
        self.assertIn("helper_function", analyzer.functions)
        self.assertIn("calculate_sum", analyzer.functions)
        self.assertIn("Calculator.add", analyzer.functions)
        self.assertIn("Calculator.subtract", analyzer.functions)

        # Verify function calls
        main_function = analyzer.functions["main"]
        self.assertIn("helper_function", main_function.calls)
        self.assertIn("calculate_sum", main_function.calls)


class TestCallGraphBuilder(unittest.TestCase):

    def test_build_call_graph(self):
        # Sample Python files
        files = {
            "main.py": """
def main():
    helper()
    result = calculator.add(1, 2)
    print(result)

if __name__ == "__main__":
    main()
""",
            "utils.py": """
def helper():
    print("Helper function")

class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""
        }

        # Build the call graph
        graph_info = build_call_graph_from_files(files)

        # Verify output structure
        self.assertIn("functions", graph_info)
        self.assertIn("file_functions", graph_info)
        self.assertIn("entry_points", graph_info)
        self.assertIn("highly_connected", graph_info)

        # Check if functions were detected
        functions = graph_info["functions"]
        self.assertIn("main", functions)

        # Check file_functions mapping
        file_functions = graph_info["file_functions"]
        self.assertIn("main.py", file_functions)
        self.assertIn("utils.py", file_functions)


class TestNonPythonFunctionsAnalyzer(unittest.TestCase):

    def test_analyze_non_python_js(self):
        # Sample JS file
        files = {
            "app.js": """
function calculateSum(a, b) {
    return a + b;
}

const multiply = (a, b) => {
    return a * b;
};

class Calculator {
    constructor() {
        this.result = 0;
    }

    add(a, b) {
        this.result = a + b;
        return this.result;
    }
}
"""
        }

        # Analyze the file
        analysis = analyze_non_python_functions(files)

        # Verify output structure
        self.assertIn("regex_detected_functions", analysis)
        self.assertIn("file_count", analysis)
        self.assertIn("function_count", analysis)

        # Check detected functions
        detected_functions = analysis["regex_detected_functions"]
        self.assertIn("app.js", detected_functions)

        js_functions = detected_functions["app.js"]
        self.assertIn("calculateSum", js_functions)
        self.assertIn("multiply", js_functions)
        self.assertIn("Calculator", js_functions)

    def test_analyze_non_python_cs(self):
        # Sample C# file
        files = {
            "Program.cs": """
using System;

namespace SampleApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello World!");
            Calculator calc = new Calculator();
            int result = calc.Add(5, 10);
            Console.WriteLine(result);
        }
    }

    class Calculator
    {
        public int Add(int a, int b)
        {
            return a + b;
        }

        public int Subtract(int a, int b)
        {
            return a - b;
        }
    }
}
"""
        }

        # Analyze the file
        analysis = analyze_non_python_functions(files)

        # Check detected functions
        detected_functions = analysis["regex_detected_functions"]
        self.assertIn("Program.cs", detected_functions)

        cs_functions = detected_functions["Program.cs"]
        self.assertIn("Main", cs_functions)
        self.assertIn("Add", cs_functions)
        self.assertIn("Subtract", cs_functions)
        self.assertIn("Program", cs_functions)
        self.assertIn("Calculator", cs_functions)


if __name__ == "__main__":
    unittest.main()