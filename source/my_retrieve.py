import os
import json
import argparse

from tqdm import tqdm
from openai import OpenAI

from dotenv import load_dotenv
from pathlib import Path

# Set the path to the .env file
env_path = Path(__file__).resolve().parent.parent / '.env'

# Load the .env file
load_dotenv(dotenv_path=env_path)

client = OpenAI()

# Load reference data from JSON files, returning a dictionary with file names as keys and content as values
def load_data_json(source_path):
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

def LLM_API(query, source_ids, corpus_dict):
    print(f"\nProcessing query: {query}...")  # Show first 100 chars of query
    print(f"Source IDs to check: {source_ids}")
    documents = []
    for file_id in source_ids:
        doc = corpus_dict.get(int(file_id))
        if doc:
            documents.append((file_id, str(doc)))
        else:
            print(f"Warning: Document ID {file_id} not found in corpus.")

    # Build context for GPT-4
    context = ''
    for file_id, doc_text in documents:
        context += f"文件 {file_id}:\n{doc_text}\n\n"

    print(f"Built context with {len(context)} characters")
    print(f"Context: {context}")  # Show first 100 chars of context

    # Prepare the prompt
    prompt = f"""你是一個有幫助的助理。根據以下參考資料，回答用戶的問題。
請根據參考資料找到最相關的文件編號。只需輸出文件編號，不要輸出其他內容。
參考資料間可能會有類似的資訊，你需要分析他們的差異，並選擇最相關的文件編號。

參考資料：
{context}

問題：
{query}


回答格式，用JSON格式：
{{
    "qid": 問題編號: int,
    "retrieve": 文件編號: int
}}"""

    # Call the GPT-4 API
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        print(f"Response: {response.choices[0].message.content}")  # Show response
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during API call: {e}")
        return None

if __name__ == "__main__":
    print("\n=== Starting Question Processing ===")
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process some paths and files.')
    parser.add_argument('--question_path', type=str, required=True, help='讀取發布題目路徑')  # Path to the question file
    parser.add_argument('--source_path', type=str, required=True, help='讀取參考資料路徑')  # Path to the reference data
    parser.add_argument('--output_path', type=str, required=True, help='輸出符合參賽格式的答案路徑')  # Path to output the answers

    args = parser.parse_args()

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
    for i, q_dict in enumerate(qs_ref['questions'], 1):
        print(f"\n--- Processing Question {i}/{len(qs_ref['questions'])} ---")
        print(f"Category: {q_dict['category']}")
        print(f"Question ID: {q_dict['qid']}")
        category = q_dict['category']
        qid = q_dict['qid']
        query = q_dict['query']
        source_ids = q_dict['source']

        if category == 'finance':
            # Retrieve the answer using GPT-4
            retrieved = LLM_API(query, source_ids, corpus_dict_finance)
            if retrieved is not None:
                try:
                    # Parse the retrieved JSON string
                    retrieved_json = json.loads(retrieved)
                    # Get the retrieve value from the parsed JSON
                    retrieve_value = int(retrieved_json.get('retrieve'))
                    answer_dict['answers'].append({"qid": qid, "retrieve": retrieve_value})
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Error parsing retrieved JSON for question ID {qid}: {e}")
            else:
                print(f"Failed to retrieve answer for question ID {qid}")

        elif category == 'insurance':
            retrieved = LLM_API(query, source_ids, corpus_dict_insurance)
            if retrieved is not None:
                try:
                    # Parse the retrieved JSON string
                    retrieved_json = json.loads(retrieved)
                    # Get the retrieve value from the parsed JSON
                    retrieve_value = int(retrieved_json.get('retrieve'))
                    answer_dict['answers'].append({"qid": qid, "retrieve": retrieve_value})
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Error parsing retrieved JSON for question ID {qid}: {e}")
            else:
                print(f"Failed to retrieve answer for question ID {qid}")

        elif category == 'faq':
            # Prepare the corpus dictionary for the FAQ category
            corpus_dict_faq = {key: str(value) for key, value in key_to_source_dict.items() if key in source_ids}
            retrieved = LLM_API(query, source_ids, corpus_dict_faq)
            if retrieved is not None:
                try:
                    # Parse the retrieved JSON string
                    retrieved_json = json.loads(retrieved)
                    # Get the retrieve value from the parsed JSON
                    retrieve_value = int(retrieved_json.get('retrieve'))
                    answer_dict['answers'].append({"qid": qid, "retrieve": retrieve_value})
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Error parsing retrieved JSON for question ID {qid}: {e}")
            else:
                print(f"Failed to retrieve answer for question ID {qid}")

        else:
            raise ValueError(f"Unknown category: {category}")

    # Save the answers to a JSON file
    print(f"\nSaving results to: {args.output_path}")
    with open(args.output_path, 'w', encoding='utf8') as f:
        json.dump(answer_dict, f, ensure_ascii=False, indent=4)
    print(f"Successfully processed {len(answer_dict['answers'])} answers")
    print("\n=== Processing Complete ===")
