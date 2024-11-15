# ESUNRAG

This project implements a PDF processing pipeline that automates the extraction, tagging, enriching, and combining of information from a collection of PDF documents. The pipeline is designed to work sequentially, with each step preparing the data for the next stage. The primary goal is to facilitate efficient information retrieval by creating a unified representation of both textual and visual data contained within PDFs.

## Overview

The pipeline consists of the following components:

1. **Extracting Page Images and Raw Text**: Extracts page images and raw text from PDF files.
2. **Tagging Content Types**: Identifies and tags pages containing images or tables.
3. **Enhancing Missing Information**: Enriches extracted data by adding metadata about images if missing in raw text.
4. **Combining Page-Level Data**: Aggregates data from different pages of the same PDF.
5. **Merging Text and Image Data**: Merges raw text with enriched image information.
6. **Retrieval-Augmented Generation (RAG)**: Utilizes combined data for efficient information retrieval.

Each step is implemented by dedicated scripts located in the `source/` directory.

## Project Structure

```
./dataset/preliminary/
    - Contains questions and predictions.

./reference/
    - Contains given data from the contest and processed data at different stages corresponding to the source code.
    - Subdirectories may include:
        - faq/
        - finance/
        - insurance/
        - finance_{process_name}/
        - insurance_{process_name}/
    - Note: Some data may have been modified manually after processing.

./source/
    - Contains source code scripts and subdirectories:
        - Preprocess/
            - Scripts for data preprocessing.
            - Includes a README detailing the preprocessing workflow.
        - Model/
            - Scripts for the retrieval method.
            - Includes a README detailing the retrieval workflow.
        - Evaluation/
            - Scripts for evaluating the model's performance.
            - Includes a README detailing the evaluation workflow.
```

## Environment

- **Operating System**: Ubuntu 22.04.4 LTS (Running on WSL)
- **CPU**: Intel(R) Core(TM) i7-11700F
- **GPU**: NVIDIA GeForce RTX 3060
- **Memory**: Total 8 GB

## Setup and Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/terry151653/ESUNRAG.git
   cd ESUNRAG
   ```

2. **Install Dependencies**:

   - Ensure you have Python 3.10.12 installed.
   - Install required Python packages:

     ```bash
     pip install -r requirements.txt
     ```

3. **Reference Setup**:

   - Place your PDF documents in the appropriate directory under `./reference/`.
   - Ensure that the directory structure matches the expected format.
   - There should be 3 subdirectories in `./reference/`: `faq/`, `finance/`, `insurance/`.

4. **Contest Reference Setup (Optional)**:

   - Due to the random nature of LLMs, the final reference data is not reproducible. If you're interested in reproducing the same results from the contest, you can unzip the provided reference data.
   ```bash
   unzip reference.zip
   ```
   - This will create 3 subdirectories in `./reference/`: `faq/`, `updated_finance_output/`, `updated_insurance_output/`.

5. **Dataset Setup**:

   - Questions are already stored in `./dataset/preliminary/`.

6. **API Keys**:

   - You need to obtain API keys for OpenAI.
   - Store these keys in environment variables in `.env` file.
   ```
   OPENAI_API_KEY="Your OpenAI API key"
   ```

## Running the Pipeline

1. **Preprocessing Steps**:
   - Follow the instructions in the [Preprocess README](source/Preprocess/README.md).

2. **Retrieval Step**:
   - Follow instructions in the [Model README](source/Model/README.md).

3. **Evaluation**:
   - Follow instructions in the [Evaluation README](source/Evaluation/README.md).

## Quick Reproduction

- To quickly reproduce the results from the contest, you can run the following command:

1. Setup processed reference data

```bash
git clone https://github.com/terry151653/ESUNRAG.git
cd ESUNRAG
pip install -r requirements.txt
unzip reference.zip
```

2. Create `.env` file and store your OpenAI API key.

3. Run the following command to reproduce the results:

```bash
python ./source/Model/my_retrieve.py \
  --question_path ./dataset/preliminary/questions_preliminary.json \
  --source_path ./reference \
  --output_path ./dataset/preliminary/pred_retrieve.json \
  --max_tasks 100
```

4. Place the prediction file in `./dataset/preliminary/`

5. Run the following command to evaluate the results:

```bash
python ./source/Evaluation/calc_precision.py \
  --predictions ./dataset/preliminary/pred_retrieve.json \
  --ground_truth ./dataset/preliminary/{ground_truth}.json
```
## Note

- The process above is the same as the contest. It will cost around 30 USD.
- If OpenAI changes the default model of `gpt-4o`, you may get different results.

## Contributing

Contributions are welcome. Please submit a pull request or open an issue for any changes or suggestions.