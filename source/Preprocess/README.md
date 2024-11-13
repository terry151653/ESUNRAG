
# Preprocessing Workflow

This directory contains the preprocessing scripts for the PDF processing pipeline. The preprocessing stage is crucial for preparing the raw data extracted from PDF documents for further processing and retrieval.

## Note

Since hand-editing is involved in the preprocessing stage, 
# if you want to reproduce the result in contest
, or you don't want to run all the scripts, you can download the reference data from [here](https://drive.google.com/drive/folders/1585555555555555555555555555555555555555?usp=sharing)
and unzip it into the `./reference` directory.

```bash
unzip reference.zip -d ./reference
```

This will unzip the final processed reference (faq, updated_finance_output, updated_insurance_output) data into the `./reference` directory.

## Workflow Overview

The preprocessing workflow consists of the following sequential steps:

### 1. Extracting Page Images and Raw Text (`ExtractPDF.py`)

- **Purpose**: Extracts both page images and raw text from each PDF document.

**Usage**:

```bash
python ExtractPDF.py --input_dir ./reference/finance --output_dir ./reference/finance_extracted
python ExtractPDF.py --input_dir ./reference/insurance --output_dir ./reference/insurance_extracted
```

### 2. Tagging Content Types (`MultiTypeTag.py`)

- **Purpose**: Tags each page to identify the presence of images or tables.

**Usage**:

```bash
python MultiTypeTag.py --input_dir ./reference/finance --output_dir ./reference/finance_extracted
python MultiTypeTag.py --input_dir ./reference/insurance --output_dir ./reference/insurance_extracted
```

### 3. Enhancing Missing Information (`MultiModel.py`)

- **Purpose**: Enriches the extracted data by OCR about images if the raw text lacks this information.
- **Methodology**:
  - Performs multimodal analysis combining text and visual data.
  - Generates image captions or descriptions for images with accompanying text.
  - Use VLM to analyze images and generate relevant descriptions.

**Usage**:

```bash
python MultiModel.py --input_dir ./reference/finance_extracted --output_dir ./reference/finance_output --max_tasks 100
python MultiModel.py --input_dir ./reference/insurance_extracted --output_dir ./reference/insurance_output --max_tasks 100
```

### 4. Combining Page-Level Data (`makeDict.py`)

- **Purpose**: Combines data extracted from different pages of the same PDF into a cohesive structure.
- **Methodology**:
  - Aggregates individual page data into a dictionary or similar data structure.
  - Organizes data for efficient access and retrieval in later stages.

**Usage**:

```bash
python makeDict.py --input_dir ./reference/finance_output --output_dir ./reference/finance_combined_output
python makeDict.py --input_dir ./reference/insurance_output --output_dir ./reference/insurance_combined_output
```

### 5. Merging Text and Image Data (`textandExtract.py`)

- **Purpose**: Merges raw text with the enriched image information to create a unified representation of the document.
- **Methodology**:
  - Integrates the extracted textual data with image metadata.
  - Ensures that both visual and textual content are available for retrieval.

**Usage**:

```bash
python textandExtract.py --text_dir ./reference/finance_extracted --json_input ./reference/finance_combined_output --json_output ./reference/updated_finance_output
python textandExtract.py --text_dir ./reference/insurance_extracted --json_input ./reference/insurance_combined_output --json_output ./reference/updated_insurance_output
```

## Additional Notes

- Ensure that all dependencies are installed before running the scripts.
- The order of execution is important; scripts should be run sequentially as listed.
- Output data from each script is used as input for the subsequent script.

## Error Handling

- If any script encounters an error, ensure that the previous steps have completed successfully.
- Check that all input files are in the correct directories and have the appropriate permissions.
