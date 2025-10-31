import json
import os
import sys


def concat_all_json_lists(directory_path, output_file):
    combined_list = []

    # Iterate over all files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):  # Process only JSON files
            file_path = os.path.join(directory_path, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Ensure the data is a list before concatenating
                    if isinstance(data, list):
                        combined_list.extend(data)  # Concatenate the list
                    else:
                        print(f"Warning: {filename} is not a list. Skipping.")

            except Exception as e:
                print(f"Error reading {filename}: {e}")

    # Write the combined list to the output file
    with open(output_file, 'w') as out_file:
        json.dump(combined_list, out_file, indent=4)

    print(f"All JSON files in {directory_path} have been concatenated into {output_file}")


# Example usage
if __name__ == '__main__':
    # Get the file path from the command line arguments
    if len(sys.argv) != 3:
        print("Usage: python read_json.py <file_path>")
    else:
        dir_path = sys.argv[1]
        merge_file_path = sys.argv[2]
        directory_path = dir_path  # Replace with your directory path
        concat_all_json_lists(directory_path, merge_file_path)