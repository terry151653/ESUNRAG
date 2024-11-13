import os
import json
import argparse
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import concurrent.futures
import logging

# Set the path to the .env file
env_path = Path(__file__).resolve().parent.parent / '.env'

# Load the .env file
load_dotenv(dotenv_path=env_path)

client = OpenAI()

# Configure logging for errors
logging.basicConfig(filename='error_log.txt', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load reference data from JSON files, returning a dictionary with file names as keys and content as values
def load_data_json(source_path: str) -> dict:
    """
    Load reference data from JSON files in the specified directory.
    
    Args:
        source_path (str): Path to directory containing JSON files
        
    Returns:
        dict: Dictionary with file IDs as keys and file content as values
        
    Example:
        If source_path contains files '1.json', '2.json', returns:
        {
            1: content_of_file_1,
            2: content_of_file_2
        }
    """
    print(f"\nLoading JSON files from: {source_path}")
    masked_file_ls = os.listdir(source_path)
    print(f"Found {len(masked_file_ls)} files")
    corpus_dict = {}
    for file in tqdm(masked_file_ls):
        if file.endswith('.json'):
            file_id = int(file.replace('.json', ''))
            file_path = os.path.join(source_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                corpus_dict[file_id] = data
    print(f"Successfully loaded {len(corpus_dict)} JSON files")
    return corpus_dict

def LLM_API(query: str, source_ids: list, corpus_dict: dict, category: str) -> str:
    """
    Process a query using the LLM API to identify the most relevant document.
    
    Args:
        query (str): User's question or query
        source_ids (list): List of document IDs to search through
        corpus_dict (dict): Dictionary containing document contents
        category (str): Type of documents ('faq', 'finance', or 'insurance')
        
    Returns:
        str: JSON string containing the most relevant document ID
        
    Example:
        Input:
            query: "How do I file a claim?"
            source_ids: [1, 2, 3]
            category: "insurance"
        Output:
            '{"retrieve": 2}'
    """
    print(f"\nProcessing query: {query}...")
    print(f"Source IDs to check: {source_ids}")
    documents = []
    for file_id in source_ids:
        doc = corpus_dict.get(int(file_id))
        if doc:
            if category == 'faq':
                documents.append((file_id, doc))
            else:
                documents.append((file_id, doc['combined_responses'], doc['raw_text']))
        else:
            print(f"Warning: Document ID {file_id} not found in corpus.")

    # Build context for LLM
    context = ''
    if category == 'faq':
        for file_id, doc in documents:
            context += f"文件 {file_id}:{{\n{{{doc}}}\n}}\n"
    else:
        for file_id, pages_text, raw_text in documents:
            context += f"文件 {file_id}:{{\npages_text:\n{{{pages_text}}}\nraw_text:\n{{{raw_text}}}\n}}\n"

    print(f"Built context with {len(context)} characters")

    prompt = f"""你是一個有幫助的助理。根據以下參考資料，回答用戶的問題。
請根據參考資料找到最相關的文件編號。只需輸出文件編號，不要輸出其他內容。
參考資料間可能會有類似的資訊，你需要分析他們的差異，並選擇最相關的文件編號。

參考資料：
{context}

問題：
{query}


回答格式，用JSON格式：
{{
    "retrieve": 文件編號: int
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0,
            response_format={"type": "json_object"}
        )

        print(f"Response: {response.choices[0].message.content}")
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during API call: {e}")
        return None

def process_question(q_dict: dict) -> dict:
    """
    Process a single question using the appropriate corpus and LLM.
    
    Args:
        q_dict (dict): Dictionary containing question details:
            {
                'category': str,  # 'finance', 'insurance', or 'faq'
                'qid': int,       # Question ID
                'query': str,     # The actual question
                'source': list    # List of source document IDs to search
            }
            
    Returns:
        dict: Dictionary containing question ID and retrieved document ID:
            {
                'qid': int,
                'retrieve': int
            }
        or None if processing fails
        
    Example:
        Input:
            {
                'category': 'insurance',
                'qid': 1,
                'query': 'How do I file a claim?',
                'source': [1, 2, 3]
            }
        Output:
            {
                'qid': 1,
                'retrieve': 2
            }
    """
    category = q_dict['category']
    qid = q_dict['qid']
    query = q_dict['query']
    source_ids = q_dict['source']

    # Access the shared data
    global corpus_dict_finance, corpus_dict_insurance, key_to_source_dict

    try:
        if category == 'finance':
            corpus_dict = corpus_dict_finance
        elif category == 'insurance':
            corpus_dict = corpus_dict_insurance
        elif category == 'faq':
            corpus_dict = {key: str(value) for key, value in key_to_source_dict.items() if key in source_ids}
        else:
            raise ValueError(f"Unknown category: {category}")

        retrieved = LLM_API(query, source_ids, corpus_dict, category)

        if retrieved is not None:
            try:
                retrieved_json = json.loads(retrieved)
                retrieve_value = int(retrieved_json.get('retrieve'))
                return {"qid": qid, "retrieve": retrieve_value}
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error parsing retrieved JSON for question ID {qid}: {e}")
        else:
            print(f"Failed to retrieve answer for question ID {qid}")
    except Exception as e:
        print(f"Exception processing question ID {qid}: {e}")
    return None

if __name__ == "__main__":
    """
    Main entry point for the document retrieval system.
    
    This script processes questions and retrieves the most relevant document IDs using LLM.
    It supports three categories of documents: finance, insurance, and FAQ.
    
    Usage:
        python my_retrieve.py --question_path /path/to/questions.json 
                            --source_path /path/to/source/dir 
                            --output_path /path/to/output.json
                            [--max_tasks 100]
    
    Args:
        question_path: Path to JSON file containing questions
        source_path: Path to directory containing reference documents
        output_path: Path where output JSON will be saved
        max_tasks: Maximum number of concurrent tasks (default: 100)
    
    The script:
    1. Loads questions from the question file
    2. Loads reference documents from the source directory
    3. Processes each question using concurrent threads
    4. Saves results to the output file in JSON format
    
    Example output format:
    {
        "answers": [
            {"qid": 1, "retrieve": 42},
            {"qid": 2, "retrieve": 17},
            ...
        ]
    }
    """
    print("\n=== Starting Question Processing ===")
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process questions and retrieve relevant documents.')
    parser.add_argument('--question_path', 
                       type=str, 
                       default="../dataset/preliminary/questions_example.json",
                       required=True, 
                       help='讀取發布題目路徑 (default: %(default)s)')
    parser.add_argument('--source_path', 
                       type=str, 
                       default="../reference",
                       required=True, 
                       help='讀取參考資料路徑 (default: %(default)s)')
    parser.add_argument('--output_path', 
                       type=str, 
                       default="../dataset/preliminary/example_pred_retrieve.json",
                       required=True, 
                       help='輸出符合參賽格式的答案路徑 (default: %(default)s)')
    parser.add_argument('--max_tasks', 
                       type=int, 
                       default=100, 
                       help='Maximum number of concurrent tasks (default: %(default)s)')

    args = parser.parse_args()
    
    print(f"Question file: {args.question_path}")
    print(f"Source directory: {args.source_path}")
    print(f"Output file: {args.output_path}")
    print(f"Max concurrent tasks: {args.max_tasks}")

    answer_dict = {"answers": []}

    # Read the question file
    print(f"\nReading questions from: {args.question_path}")
    with open(args.question_path, 'r', encoding='utf-8') as f:
        qs_ref = json.load(f)
    print(f"Loaded {len(qs_ref['questions'])} questions")

    # Load reference data
    source_path_insurance = os.path.join(args.source_path, 'updated_insurance_output')
    corpus_dict_insurance = load_data_json(source_path_insurance)

    source_path_finance = os.path.join(args.source_path, 'updated_finance_output')
    corpus_dict_finance = load_data_json(source_path_finance)

    with open(os.path.join(args.source_path, 'faq', 'pid_map_content.json'), 'r', encoding='utf-8') as f_s:
        key_to_source_dict = json.load(f_s)
        # Ensure keys are integers
        key_to_source_dict = {int(key): value for key, value in key_to_source_dict.items()}

    print("\nProcessing questions...")

    # Create list to store all tasks
    all_tasks = qs_ref['questions']
    max_concurrent_tasks = args.max_tasks
    error_count = 0
    total_tasks = len(all_tasks)
    task_index = 0  # Index to keep track of the next task to submit

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_tasks) as executor:
        futures = {}  # Dictionary to map futures to q_dict

        while task_index < total_tasks or futures:
            # Submit new tasks if we have less than max_concurrent_tasks running and there are tasks left
            while len(futures) < max_concurrent_tasks and task_index < total_tasks:
                q_dict = all_tasks[task_index]
                future = executor.submit(process_question, q_dict)
                futures[future] = q_dict  # Store the entire q_dict
                task_index += 1
                print(f"Submitted task {task_index}/{total_tasks}: Question ID {q_dict['qid']}")

            # Wait for any future to complete
            done, _ = concurrent.futures.wait(futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)

            # Remove completed futures and update error count
            for future in done:
                q_dict = futures.pop(future)
                result = future.result()
                if result:
                    if result['qid'] != q_dict['qid']:
                        print(f"QID mismatch for question ID {q_dict['qid']}")
                        error_count += 1
                    else:
                        answer_dict['answers'].append(result)
                        print(f"Completed task: Question ID {result['qid']}")
                else:
                    print(f"Failed to process question ID {q_dict['qid']}")
                    error_count += 1

        # Ensure all futures are done
        concurrent.futures.wait(futures.keys())

    # Sort answers by qid before saving
    answer_dict['answers'].sort(key=lambda x: x['qid'])

    # Save the answers to a JSON file
    print(f"\nSaving results to: {args.output_path}")
    with open(args.output_path, 'w', encoding='utf8') as f:
        json.dump(answer_dict, f, ensure_ascii=False, indent=4)
    print(f"Successfully processed {len(answer_dict['answers'])} answers")
    print(f"Total number of errors: {error_count}")
    print("\n=== Processing Complete ===")
