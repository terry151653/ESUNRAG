import os
import json
import re

def combine_json_files(directory, output_dir):
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
    # Specify the input and output directories
    input_dir = "../reference/insurance_output"
    output_dir = "../reference/insurance_combined_output"
    
    # Run the combine function
    results = combine_json_files(input_dir, output_dir)
    print("JSON files have been combined successfully!")
