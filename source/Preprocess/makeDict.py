import os
import json
import re
import argparse

def combine_json_files(directory: str, output_dir: str) -> dict:
    """
    Combines multiple JSON files with matching number prefixes into single files.
    
    This function processes JSON files in the input directory that have numeric prefixes
    (e.g., '1_xxx.json', '1_yyy.json') and combines files with matching prefixes into
    single output files (e.g., '1.json').
    
    Args:
        directory (str): Path to the directory containing input JSON files
        output_dir (str): Path to the directory where combined files will be saved
        
    Returns:
        dict: A dictionary mapping number prefixes to lists of combined responses
        
    Example:
        Input files:
            - 1_response1.json
            - 1_response2.json
            - 2_response1.json
        Output files:
            - 1.json (contains responses from both 1_*.json files)
            - 2.json (contains response from 2_*.json)
    """
    # Dictionary to store combined results
    combined_results = {}
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Walk through all files in directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            # Extract the number prefix using regex
            match = re.match(r'(\d+)_', filename)
            if match:
                number_prefix = match.group(1)
                
                # Read JSON file
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        
                        # Get response content
                        if 'response' in data:
                            # Initialize list for this number if not exists
                            if number_prefix not in combined_results:
                                combined_results[number_prefix] = []
                                
                            # Add response to list
                            combined_results[number_prefix].append(data['response'])
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON from file: {filename}")
                        continue
    
    # Save combined results
    for number, responses in combined_results.items():
        output_filename = os.path.join(output_dir, f'{number}.json')
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'combined_responses': responses
            }, f, ensure_ascii=False, indent=2)
            
    return combined_results

if __name__ == "__main__":
    """
    Main entry point for JSON file combination script.
    
    This script combines multiple JSON files with the same number prefix into single files.
    For example, files like '1_xxx.json', '1_yyy.json' will be combined into '1.json'.
    
    Usage:
        python makeDict.py --input_dir /path/to/input --output_dir /path/to/output
    
    The output JSON files will contain all responses in a 'combined_responses' array.
    """
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Combine JSON files with matching number prefixes.')
    parser.add_argument('--input_dir', 
                       type=str,
                       default="../reference/test_output",
                       help='Directory containing JSON files to combine')
    parser.add_argument('--output_dir',
                       type=str,
                       default="../reference/test_combined_output",
                       help='Directory where combined JSON files will be saved')
    
    args = parser.parse_args()
    
    print(f"Reading JSON files from: {args.input_dir}")
    print(f"Saving combined files to: {args.output_dir}")
    
    # Run the combine function
    results = combine_json_files(args.input_dir, args.output_dir)
    print("JSON files have been combined successfully!")
