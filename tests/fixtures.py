import os
import tempfile
import shutil
from pathlib import Path


def create_sample_repo():
    """Create a sample repository for testing"""
    temp_dir = tempfile.mkdtemp()

    # Create some Python files
    py_file1_path = os.path.join(temp_dir, "main.py")
    with open(py_file1_path, "w") as f:
        f.write("""
def main():
    print("Hello, world!")
    calculate_sum(1, 2)

def calculate_sum(a, b):
    return a + b

if __name__ == "__main__":
    main()
""")

    py_file2_path = os.path.join(temp_dir, "utils.py")
    with open(py_file2_path, "w") as f:
        f.write("""
from datetime import datetime

def get_current_time():
    return datetime.now()

def format_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")
""")

    # Create a requirements.txt file
    req_path = os.path.join(temp_dir, "requirements.txt")
    with open(req_path, "w") as f:
        f.write("""
pytest==7.3.1
click>=8.0.0
rich>=10.0.0
""")

    # Create a C# file
    csharp_dir = os.path.join(temp_dir, "csharp")
    os.makedirs(csharp_dir, exist_ok=True)
    cs_file_path = os.path.join(csharp_dir, "Program.cs")
    with open(cs_file_path, "w") as f:
        f.write("""
using System;

namespace SampleApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, world!");
            var result = Calculator.Add(5, 10);
            Console.WriteLine($"5 + 10 = {result}");
        }
    }

    class Calculator
    {
        public static int Add(int a, int b)
        {
            return a + b;
        }
    }
}
""")

    # Create a React component
    react_dir = os.path.join(temp_dir, "react")
    os.makedirs(react_dir, exist_ok=True)
    jsx_file_path = os.path.join(react_dir, "App.jsx")
    with open(jsx_file_path, "w") as f:
        f.write("""
import React, { useState } from 'react';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <h1>Counter: {count}</h1>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}

export default App;
""")

    # Create a package.json file
    pkg_path = os.path.join(react_dir, "package.json")
    with open(pkg_path, "w") as f:
        f.write("""
{
  "name": "sample-app",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "eslint": "^8.36.0"
  }
}
""")

    return temp_dir


def cleanup_sample_repo(repo_path):
    """Clean up the sample repository after testing"""
    shutil.rmtree(repo_path)