# RAG System

This document provides instructions and information about the `my_retrieve.py` script, a document retrieval system that processes questions and identifies the most relevant documents using a Large Language Model (LLM). The script supports three categories of documents: **finance**, **insurance**, and **FAQ**.

## Overview

The `my_retrieve.py` script processes user queries by searching through a set of reference documents and determining the most relevant document for each query. It leverages the OpenAI API to utilize a powerful language model for understanding and processing queries and documents.

## Usage

Run the script using the following command:

```bash
python ./source/Model/my_retrieve.py --question_path /path/to/questions.json --source_path /path/to/reference_dir --output_path /path/to/output.json --max_tasks 100
```

### Command-Line Arguments

- `--question_path`: **(Required)** Path to the JSON file containing the questions.

- `--source_path`: **(Required)** Path to the directory containing the reference documents.

- `--output_path`: **(Required)** Path where the output JSON file with the results will be saved.

- `--max_tasks`: *(Optional)* Maximum number of concurrent tasks (threads) to use while processing questions. Default is `100`.

### Example

```bash
python ./source/Model/my_retrieve.py \
  --question_path ./dataset/preliminary/questions_example.json \
  --source_path ./reference \
  --output_path ./dataset/preliminary/example_pred_retrieve.json \
  --max_tasks 50
```

## Input File Formats

### Questions File (`questions_example.json`)

The questions file should be a JSON file with the following structure:

```json
{
  "questions": [
    {
      "qid": 1,
      "category": "insurance",
      "query": "How do I file a claim?",
      "source": [101, 102, 103]
    },
    {
      "qid": 2,
      "category": "finance",
      "query": "What are the current interest rates?",
      "source": [201, 202, 203]
    }
    // More questions...
  ]
}
```

- `qid`: Unique question ID.
- `category`: One of `"finance"`, `"insurance"`, or `"faq"`.
- `query`: The user's question.
- `source`: List of document IDs to search through.

## Output

The script produces a JSON file containing the answers:

```json
{
  "answers": [
    {
      "qid": 1,
      "retrieve": 102
    },
    {
      "qid": 2,
      "retrieve": 201
    }
    // More answers...
  ]
}
```

- Each entry maps the `qid` (question ID) to the `retrieve` (the most relevant document ID as determined by the language model).

## Logging and Error Handling

- **Logging**: Errors are logged to a file named `error_log.txt` in the current directory.

- **Error Count**: The script keeps track of the number of errors encountered during processing and displays the total count upon completion.

- **Common Errors**:

  - **Warning**: If a document ID in `source_ids` is not found in the corpus, a warning is printed.
  - **JSON Parsing Errors**: If the API response cannot be parsed, an error message is displayed.

## Important Notes

- **OpenAI API Model Selection**: The script uses the model `"gpt-4o"` in the API call. Ensure you have access to this model or adjust the `model` parameter in the script as necessary.

- **API Rate Limits**: Be mindful of OpenAI API rate limits, especially when setting a high value for `--max_tasks`.

- **Data Integrity**: Ensure that all reference documents and question files are correctly formatted and accessible.

## Customization

- Parameters in the script now is the default value, you should not change if you want to reproduce the result.

- **Adjusting the Model**: You can change the `model` parameter in the `LLM_API` function to use a different OpenAI model if needed.

- **Temperature and Max Tokens**: Modify the `temperature` and `max_tokens` parameters in the API call to adjust the creativity and length of the responses.

## Troubleshooting

- **No Relevant Data Found**: If the script cannot find relevant data, verify that the reference documents are correctly loaded and that the document IDs match.

- **API Errors**: Check your OpenAI API key and ensure that you have sufficient access and that the API service is operational.

- **Performance Issues**: If you encounter performance issues or rate limit errors, try reducing the `--max_tasks` value.