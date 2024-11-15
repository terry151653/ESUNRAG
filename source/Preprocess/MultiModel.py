import os
import json
import base64
from openai import OpenAI
from typing import List, Dict, Any, Optional
import concurrent.futures
import logging
from dotenv import load_dotenv
from pathlib import Path

# Set the path to the .env file
env_path = Path(__file__).resolve().parent.parent / '.env'

# Load the .env file
load_dotenv(dotenv_path=env_path)

# Configure logging for errors
logging.basicConfig(filename='error_log.txt', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MultiModel:
    def __init__(self):
        """Initialize the MultiModel with OpenAI API key"""
        self.client = OpenAI()

    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_content(self, text: str, image_paths: Optional[List[str]] = None, prompt: str = "") -> Dict[str, Any]:
        """
        Analyze content using GPT-4 Vision model with text and optional multiple image inputs
        
        Args:
            text: Text input to analyze
            image_paths: Optional list of paths to image files
            prompt: Prompt/instructions for the model
            
        Returns:
            Dict containing model response and metadata
        """
        try:
            # Construct base message content
            content = [{"type": "text", "text": text}]
            
            # Add images if provided
            if image_paths:
                for image_path in image_paths:
                    base64_image = self.encode_image(image_path)
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content}
            ]
            
            # Use vision model
            model = "gpt-4o"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Define a function to process a task
def process_task(task):
    try:
        # Use the pre-initialized model
        result = model.analyze_content(
            text=task['text'],
            image_paths=task['image_paths'],
            prompt=task['prompt']
        )
        os.makedirs(os.path.dirname(task['output_path']), exist_ok=True)
        with open(task['output_path'], 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        # Log error details
        error_message = f"Error processing task for {task['output_path']}: {e}"
        print(error_message)
        logging.error(error_message)
        return False
    

if __name__ == "__main__":
    """
    Main entry point for MultiModel content analysis script.
    
    This script processes PDF content (text and images) using GPT-4o model.
    It analyzes content from extracted PDF directories and generates JSON outputs
    containing the analyzed information.
    
    Usage:
        python MultiModel.py --input_dir /path/to/input --output_dir /path/to/output --max_tasks 100
        
    The input directory should contain subdirectories with extracted PDF content
    (text files and images) generated by ExtractPDF.py and tagged by MultiTypeTag.py.
    """
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Analyze PDF content using GPT-4o model.')
    parser.add_argument('--input_dir', 
                       type=str,
                       default="./reference/test_extracted/",
                       help='Directory containing extracted PDF content')
    parser.add_argument('--output_dir',
                       type=str,
                       default="./reference/test_output/",
                       help='Directory where analysis results will be saved')
    parser.add_argument('--max_tasks',
                       type=int,
                       default=100,
                       help='Maximum number of concurrent tasks')
    
    args = parser.parse_args()
    
    print(f"Processing content from: {args.input_dir}")
    print(f"Saving results to: {args.output_dir}")
    print(f"Maximum concurrent tasks: {args.max_tasks}")
    
    system_prompt = """You're a helpful assistant that can extract detailed information from the input text and images.
You will be provided with:
1. The parsed text from the entire PDF document
2. A specific image of one page from the PDF document

Your task is to extract the information from the image and combine it with the corresponding part of the parsed text, especially if any information is missing from the text. Your output should be focused on capturing the complete information contained in the page image in detail, in raw text form.

Make sure your response is comprehensive enough that a chinese reader would fully understand the content of the page even without seeing the original document.

**Output Requirements:**
- The output must be in JSON format, structured as follows:
  
  ```json
  {
    "page{n}_text": "Extracted information from the image combined with the parsed text for page n. The text should be complete enough for readers to understand the content."
  }

"""
    
    # Initialize MultiModel (you'll need to add your API key here)
    model = MultiModel()
    
    # Create list to store all tasks
    all_tasks = []
    error_count = 0

    # Iterate through numbered directories
    for dir_name in os.listdir(args.input_dir):
        dir_path = os.path.join(args.input_dir, dir_name)
        if not os.path.isdir(dir_path):
            continue
            
        # Find text file and check for images/tables
        files = os.listdir(dir_path)
        has_pic = any(f.startswith('hasPic') for f in files)
        has_table = any(f.startswith('hasTable') for f in files)

        # Find the text file
        text_file = next((f for f in files if f.endswith('.txt')), None)
        if not text_file:
            print(f"No text file found in {dir_path}")
            continue

        # Read text content
        with open(os.path.join(dir_path, text_file), 'r', encoding='utf-8') as f:
            text_content = f.read()

        # Process each image individually if pictures are present
        if has_pic:
            image_files = [f for f in files if f.endswith('.png')]

            for idx, image_file in enumerate(image_files, 1):
                image_path = os.path.join(dir_path, image_file)

                # Add task for each image
                all_tasks.append({
                    'text': text_content,
                    'image_paths': [image_path],
                    'prompt': system_prompt,
                    'output_path': os.path.join(args.output_dir, f"{dir_name}_image{idx}_result.json")
                })

        else:
            # Add text-only task
            all_tasks.append({
                'text': text_content,
                'image_paths': None,
                'prompt': system_prompt,
                'output_path': os.path.join(args.output_dir, f"{dir_name}_result.json")
            })

        print(f"Prepared tasks for directory {dir_name}")

    # Process tasks with the specified concurrent task limit
    max_concurrent_tasks = args.max_tasks
    error_count = 0
    total_tasks = len(all_tasks)
    task_index = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_tasks) as executor:
        futures = {}  # Dictionary to map futures to tasks

        while task_index < total_tasks or futures:
            # Submit new tasks if we have less than 100 running and there are tasks left
            while len(futures) < max_concurrent_tasks and task_index < total_tasks:
                task = all_tasks[task_index]
                future = executor.submit(process_task, task)
                futures[future] = task
                task_index += 1
                print(f"Submitted task {task_index}/{total_tasks}: {task['output_path']}")

            # Wait for any future to complete
            done, _ = concurrent.futures.wait(futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)

            # Remove completed futures and update error count
            for future in done:
                task = futures.pop(future)
                result = future.result()
                if not result:
                    error_count += 1
                print(f"Completed task: {task['output_path']}")

        # Ensure all futures are done
        concurrent.futures.wait(futures.keys())

    # Print total number of errors encountered
    print(f"Total number of errors: {error_count}")