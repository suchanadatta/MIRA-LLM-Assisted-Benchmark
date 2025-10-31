import json
import sys


def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the file.")
        return None
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None


if __name__ == "__main__":
    # Get the file path from the command line arguments
    if len(sys.argv) != 2:
        print("Usage: python read_json.py <file_path>")
    else:
        file_path = sys.argv[1]
        data = read_json_file(file_path)
        if data:
            print("Successfully loaded JSON data:", file_path)
