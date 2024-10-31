import fitz  # PyMuPDF
import os

def has_images(pdf_path):
    """
    Check if a PDF file contains any images
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        bool: True if PDF contains images, False otherwise
    """
    try:
        
        doc = fitz.open(pdf_path)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            if page.get_images():
                doc.close()
                return True
                
        doc.close()
        return False
        
    except Exception as e:
        print(f"Error checking for images: {str(e)}")
        return False

def has_tables(pdf_path):
    """
    Check if a PDF file contains any tables
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        bool: True if PDF contains tables, False otherwise
    """
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            # Check for tables using text analysis
            # Look for consistent vertical alignment and multiple columns
            words = page.get_text("words")
            if len(words) > 0:
                # Group words by their vertical position
                y_positions = {}
                for word in words:
                    y_pos = round(word[3])  # bottom y-coordinate
                    if y_pos in y_positions:
                        y_positions[y_pos] += 1
                    else:
                        y_positions[y_pos] = 1
                
                # If we have multiple words aligned on the same y-position
                # it might indicate a table
                for count in y_positions.values():
                    if count >= 3:  # At least 3 words aligned horizontally
                        doc.close()
                        return True
        
        doc.close()
        return False
        
    except Exception as e:
        print(f"Error checking for tables: {str(e)}")
        return False

if __name__ == "__main__":
    input_dir = "../"
    output_dir = "../"
    for pdf_file in os.listdir(input_dir):
        if not pdf_file.endswith('.pdf'):
            continue
            
        pdf_path = os.path.join(input_dir, pdf_file)
        pdf_name = os.path.splitext(pdf_file)[0]
        pdf_output_dir = os.path.join(output_dir, pdf_name)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(pdf_output_dir):
            os.makedirs(pdf_output_dir)
        
        # Check for images and tables
        has_img = has_images(pdf_path)
        has_tbl = has_tables(pdf_path)
        
        # Create status files
        if has_img:
            with open(os.path.join(pdf_output_dir, "hasPic"), "w") as f:
                pass
        else:
            with open(os.path.join(pdf_output_dir, "noPic"), "w") as f:
                pass
                
        if has_tbl:
            with open(os.path.join(pdf_output_dir, "hasTable"), "w") as f:
                pass
        else:
            with open(os.path.join(pdf_output_dir, "noTable"), "w") as f:
                pass
        
        print(f"{pdf_file}: Images: {'Yes' if has_img else 'No'}, Tables: {'Yes' if has_tbl else 'No'}")