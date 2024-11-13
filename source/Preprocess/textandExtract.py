import os
import json
import argparse

def combine_text_and_json(text_root_dir: str, json_input_dir: str, json_output_dir: str) -> None:
    """
    Combines text files with their corresponding JSON files.
    
    This function reads text content from files in the text directory and adds it to
    corresponding JSON files under the 'raw_text' key. The updated JSON files are saved
    to the output directory.
    
    Args:
        text_root_dir (str): Directory containing subdirectories with text files
        json_input_dir (str): Directory containing input JSON files
        json_output_dir (str): Directory where updated JSON files will be saved
        
    Example:
        Input structure:
            text_root_dir/
                doc1/
                    doc1_text.txt
                doc2/
                    doc2_text.txt
            json_input_dir/
                doc1.json
                doc2.json
    """
    # Create the output directory if it doesn't exist
    os.makedirs(json_output_dir, exist_ok=True)

    # Iterate over all subdirectories in the text root directory
    for subdir in os.listdir(text_root_dir):
        text_subdir_path = os.path.join(text_root_dir, subdir)
        if os.path.isdir(text_subdir_path):
            # Construct the expected text file path
            text_file_path = os.path.join(text_subdir_path, f"{subdir}_text.txt")
            
            # Check if the text file exists
            if os.path.isfile(text_file_path):
                # Read the text content from the text file
                with open(text_file_path, 'r', encoding='utf-8') as text_file:
                    text_content = text_file.read()
                
                # Construct the corresponding JSON file path
                json_file_name = f"{subdir}.json"
                json_file_path = os.path.join(json_input_dir, json_file_name)
                
                # Check if the JSON file exists
                if os.path.isfile(json_file_path):
                    # Read the existing data from the JSON file
                    with open(json_file_path, 'r', encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                    
                    # Add the text content to the JSON data under the key "raw_text"
                    json_data['raw_text'] = text_content
                    
                    # Construct the output JSON file path
                    output_json_file_path = os.path.join(json_output_dir, json_file_name)
                    
                    # Write the updated JSON data to the new directory
                    with open(output_json_file_path, 'w', encoding='utf-8') as json_file:
                        json.dump(json_data, json_file, ensure_ascii=False, indent=4)
                    
                    print(f"Processed and saved: {output_json_file_path}")
                else:
                    print(f"JSON file not found: {json_file_path}")
            else:
                print(f"Text file not found: {text_file_path}")

if __name__ == "__main__":
    """
    Main entry point for text and JSON combination script.
    
    This script combines text content from extracted files with their corresponding
    JSON files, adding the text under a 'raw_text' key.
    
    Usage:
        python textandExtract.py --text_dir /path/to/text --json_input /path/to/json --json_output /path/to/output
    """
    parser = argparse.ArgumentParser(description='Combine text files with JSON files.')
    parser.add_argument('--text_dir', 
                       type=str,
                       default="../reference/test_extracted",
                       help='Directory containing text files in subdirectories')
    parser.add_argument('--json_input',
                       type=str,
                       default="../reference/test_combined_output",
                       help='Directory containing input JSON files')
    parser.add_argument('--json_output',
                       type=str,
                       default="../reference/updated_test_output",
                       help='Directory where updated JSON files will be saved')
    
    args = parser.parse_args()
    
    print(f"Reading text files from: {args.text_dir}")
    print(f"Reading JSON files from: {args.json_input}")
    print(f"Saving updated files to: {args.json_output}")
    
    combine_text_and_json(args.text_dir, args.json_input, args.json_output)
    print("\nProcessing complete!")
