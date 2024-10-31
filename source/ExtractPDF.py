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
            # Extract tables first
            tables = page.extract_tables()
            
            # Get all table bounding boxes
            table_areas = []
            for table in page.find_tables():
                x0, y0, x1, y1 = table.bbox
                # Ensure y0 is smaller than y1 (top should be smaller than bottom)
                if y0 > y1:
                    y0, y1 = y1, y0
                table_areas.append((x0, y0, x1, y1))
            
            # Sort table areas by vertical position (top to bottom)
            table_areas.sort(key=lambda x: x[1])
            
            # Extract text from non-table areas
            if table_areas:
                # Get the full page dimensions
                x0, top, x1, bottom = page.bbox
                
                # Create a list of vertical sections to extract text from
                text = ""
                
                # Add text before first table
                if table_areas[0][1] > top:
                    section = (x0, top, x1, table_areas[0][1])
                    crop = page.within_bbox(section)
                    if crop:
                        text += crop.extract_text() or ""
                
                # Add text between tables
                for i in range(len(table_areas) - 1):
                    section = (x0, table_areas[i][3], x1, table_areas[i+1][1])
                    crop = page.within_bbox(section)
                    if crop:
                        text += crop.extract_text() or ""
                
                # Add text after last table
                if table_areas[-1][3] < bottom:
                    section = (x0, table_areas[-1][3], x1, bottom)
                    crop = page.within_bbox(section)
                    if crop:
                        text += crop.extract_text() or ""
            else:
                text = page.extract_text()
                
            if text:
                result['text'] += text.strip() + '\n'
            
            # Add formatted tables
            if tables:
                result['text'] += f"\n=== TABLES ON PAGE {page_num + 1} ===\n"
                for table_num, table in enumerate(tables):
                    result['text'] += f"\nTable {table_num + 1}:\n"
                    
                    # Convert table to text format
                    for row in table:
                        row = [str(cell or '').strip() for cell in row]
                        result['text'] += ' | '.join(row) + '\n'
                    
                    result['text'] += '\n'  # Add extra line between tables
                    
                    # Save CSV if needed
                    table_path = os.path.join(output_dir, f'{pdf_name}_page_{page_num + 1}_table_{table_num + 1}.csv')
                    with open(table_path, 'w', encoding='utf-8', newline='') as f:
                        import csv
                        writer = csv.writer(f)
                        writer.writerows(table)
                    result['tables'].append(table_path)
    
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