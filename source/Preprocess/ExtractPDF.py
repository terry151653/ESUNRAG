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
        'images': []
    }
    
    # Extract text using pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_content = []
            seen_content = set()
            
            # Get page boundaries
            page_x0, page_y0, page_x1, page_y1 = page.bbox
            
            # Extract tables and their positions
            tables = page.extract_tables()
            for table_num, table in enumerate(tables):
                try:
                    table_obj = page.find_tables()[table_num]
                    x0, y0, x1, y1 = table_obj.bbox
                    
                    # Ensure coordinates are within page bounds
                    x0 = max(x0, page_x0)
                    y0 = max(y0, page_y0)
                    x1 = min(x1, page_x1)
                    y1 = min(y1, page_y1)
                    
                    # Skip tables with invalid dimensions
                    if x1 - x0 <= 0 or y1 - y0 <= 0:
                        continue
                    
                    # Process table rows
                    table_text = ""
                    for row in table:
                        if not any(cell for cell in row):
                            continue
                        cleaned_cells = [str(cell or '').strip() for cell in row]
                        if any(cleaned_cells):
                            row_text = ' | '.join(cleaned_cells)
                            if row_text not in seen_content:
                                table_text += row_text + '\n'
                                seen_content.add(row_text)
                    
                    if table_text:
                        page_content.append((y0, table_text))
                except Exception as e:
                    print(f"Warning: Skipping problematic table on page {page_num + 1}: {str(e)}")
                    continue
            
            # Extract regular text with boundary validation
            words = page.extract_words(keep_blank_chars=True)
            current_line = []
            current_y = None
            line_spacing_threshold = 3
            
            for word in words:
                # Validate word position is within page bounds
                if not (page_y0 <= word['top'] <= page_y1):
                    continue
                    
                if current_y is None:
                    current_y = word['top']
                
                if abs(word['top'] - current_y) > line_spacing_threshold:
                    if current_line:
                        text = ' '.join(current_line).strip()
                        if text.endswith('-'):
                            text = text[:-1]
                        elif not text.endswith('.'):
                            text += ' '
                            
                        if text and text not in seen_content:
                            page_content.append((current_y, text))
                            seen_content.add(text)
                    
                    current_line = [word['text']]
                    current_y = word['top']
                else:
                    current_line.append(word['text'])
            
            # Process last line
            if current_line:
                text = ' '.join(current_line).strip()
                if text.endswith('-'):
                    text = text[:-1]
                if text and text not in seen_content:
                    page_content.append((current_y, text))
                    seen_content.add(text)
            
            # Sort all content by vertical position and combine
            page_content.sort(key=lambda x: x[0])
            page_text = '\n'.join(content for _, content in page_content)
            if page_text:
                result['text'] += page_text.strip() + '\n\n'

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
            # Updated print statement to only show pages (removed tables reference)
            print(f"Processed {pdf_file}: {len(content['images'])} pages extracted")
        except Exception as e:
            error_count += 1
            print(f"Error processing {pdf_file}: {str(e)}")
    
    print(f"\nProcessing complete. Total errors: {error_count}")
    return error_count
if __name__ == "__main__":
    """
    Main entry point for PDF processing script.
    
    Usage:
        python ExtractPDF.py --input_dir /path/to/pdfs --output_dir /path/to/output
    """
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract text and images from PDF files.')
    parser.add_argument('--input_dir', 
                       type=str,
                       default="../reference/test",
                       help='Directory containing PDF files to process')
    parser.add_argument('--output_dir',
                       type=str,
                       default="../reference/test_extracted",
                       help='Directory where extracted content will be saved')
    
    args = parser.parse_args()
    
    print(f"Processing PDFs from: {args.input_dir}")
    print(f"Saving output to: {args.output_dir}")
    
    total_errors = process_pdf_directory(args.input_dir, args.output_dir)
    print(f"Total errors across all PDFs: {total_errors}")