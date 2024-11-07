import os
import pdfplumber
import fitz  # PyMuPDF for image extraction

def extract_pdf_content(pdf_path, output_dir):
    """
    Extract both text and page images from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images
    
    Returns:
        dict: Dictionary containing extracted text and image paths
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Define pdf_name at the start of the function
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    result = {
        'text': '',
        'images': [],
        'tables': []
    }
    
    # Extract text and tables using pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_content = []  # List to store all content with their positions
            seen_content = set()  # Track unique content per page
            
            # Extract tables with their positions
            tables = page.extract_tables()
            table_texts = set()  # Store all table text for duplicate checking
            
            for table_num, table in enumerate(tables):
                table_obj = page.find_tables()[table_num]
                y_pos = table_obj.bbox[1]  # Get y position of table
                
                # Only add page header for first table on page
                table_text = f"=== TABLES ON PAGE {page_num + 1} ===\n\n" if table_num == 0 else "\n"
                
                # Process table rows without adding "Table X:" header
                for row in table:
                    if not any(cell for cell in row):
                        continue
                    cleaned_cells = []
                    for cell in row:
                        cell_text = str(cell or '').strip()
                        cleaned_cells.append(cell_text)
                    if any(cleaned_cells):
                        row_text = ' | '.join(cleaned_cells)
                        if row_text not in seen_content:
                            table_text += row_text + '\n'
                            seen_content.add(row_text)
                            # Add individual cells to seen content
                            for cell in cleaned_cells:
                                if cell:
                                    seen_content.add(cell)
                                    table_texts.add(cell)
                
                # Add table to content list with its position
                page_content.append((y_pos, table_text))
                
                # Save CSV
                table_path = os.path.join(output_dir, f'{pdf_name}_page_{page_num + 1}_table_{table_num + 1}.csv')
                with open(table_path, 'w', encoding='utf-8', newline='') as f:
                    import csv
                    writer = csv.writer(f)
                    writer.writerows(table)
                result['tables'].append(table_path)
            
            # Extract words with their positions
            words = page.extract_words(keep_blank_chars=True)  # Keep blank chars for better spacing
            current_line = []
            current_y = None
            line_spacing_threshold = 3  # Adjust this value if needed
            
            # Group words into lines with better handling of line breaks
            for word in words:
                if current_y is None:
                    current_y = word['top']
                
                # Check if this is a new line
                if abs(word['top'] - current_y) > line_spacing_threshold:
                    # Process previous line
                    if current_line:
                        text = ' '.join(current_line).strip()
                        # Check if the line ends with a hyphen (possible word break)
                        if text.endswith('-'):
                            text = text[:-1]  # Remove hyphen
                        elif not text.endswith('.'):  # Not end of sentence
                            text += ' '  # Add space for continuation
                            
                        if (text and 
                            text not in seen_content and 
                            not any(text in content for _, content in page_content) and
                            not any(text in table_text for table_text in table_texts)):
                            page_content.append((current_y, text))
                            seen_content.add(text)
                    
                    current_line = [word['text']]
                    current_y = word['top']
                else:
                    # Add space between words if needed
                    if current_line and not current_line[-1].endswith('-'):
                        current_line.append(word['text'])
                    else:
                        current_line.append(word['text'])
            
            # Process last line
            if current_line:
                text = ' '.join(current_line).strip()
                if text.endswith('-'):
                    text = text[:-1]
                    
                if (text and 
                    text not in seen_content and 
                    not any(text in content for _, content in page_content) and
                    not any(text in table_text for table_text in table_texts)):
                    page_content.append((current_y, text + '\n'))
                    seen_content.add(text)
            
            # Sort and combine content
            page_content.sort(key=lambda x: x[0])
            
            # Combine lines more intelligently
            current_text = ''
            for _, content in page_content:
                if content.startswith('==='):
                    if current_text:
                        result['text'] += current_text.strip() + '\n'
                        current_text = ''
                    result['text'] += content
                elif '|' in content:
                    if current_text:
                        result['text'] += current_text.strip() + '\n'
                        current_text = ''
                    result['text'] += content
                else:
                    if current_text:
                        current_text += ' '
                    current_text += content.strip()
            
            if current_text:
                result['text'] += current_text.strip() + '\n'
    
    # Final cleanup - simpler version that preserves original spacing
    lines = []
    seen_lines = set()
    
    for line in result['text'].split('\n'):
        line = line.strip()
        if line.startswith('==='):
            if lines:
                lines.append('')
            lines.append(line)
            lines.append('')
        elif line and line not in seen_lines:
            lines.append(line)
            seen_lines.add(line)
        elif not line and (not lines or lines[-1]):
            lines.append(line)
    
    result['text'] = '\n'.join(lines)
    
    # Save extracted text to file
    text_path = os.path.join(output_dir, f'{pdf_name}_text.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(result['text'])
    
    # Extract full page images using PyMuPDF
    doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # Set high resolution parameters
        zoom = 4.0  # Increase zoom factor for higher resolution
        mat = fitz.Matrix(zoom, zoom)
        
        # Convert page to high-res pixmap
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # Save page image in high quality
        image_path = os.path.join(output_dir, f'{pdf_name}_page_{page_num + 1}.png')
        pix.save(image_path, output="png")
        result['images'].append(image_path)
    
    doc.close()
    return result

def process_pdf_directory(input_dir, output_dir):
    """
    Process all PDFs in a directory and extract their contents
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory to save extracted contents
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    
    # Add error counter
    error_count = 0
    
    # Process each PDF file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        # Create subdirectory for each PDF
        pdf_output_dir = os.path.join(output_dir, os.path.splitext(pdf_file)[0])
        
        try:
            content = extract_pdf_content(pdf_path, pdf_output_dir)
            print(f"Processed {pdf_file}: {len(content['images'])} pages and {len(content['tables'])} tables extracted")
        except Exception as e:
            error_count += 1
            print(f"Error processing {pdf_file}: {str(e)}")
    
    print(f"\nProcessing complete. Total errors: {error_count}")
    return error_count

if __name__ == "__main__":
    # Example usage
    input_dir = "../"
    output_dir = "../"
    
    total_errors = process_pdf_directory(input_dir, output_dir)
    print(f"Total errors across all PDFs: {total_errors}")