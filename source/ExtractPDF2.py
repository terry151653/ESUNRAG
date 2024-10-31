import os
import pdfplumber
import fitz
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

def images_are_similar(img1_path, img2_path, threshold=0.8):
    """Compare two images for similarity"""
    try:
        img1 = Image.open(img1_path).convert('L')  # Convert to grayscale
        img2 = Image.open(img2_path).convert('L')
        
        # Resize images to same size for comparison
        img2 = img2.resize(img1.size)
        
        # Convert to numpy arrays
        arr1 = np.array(img1, dtype=np.float32)
        arr2 = np.array(img2, dtype=np.float32)
        
        # Handle uniform images
        if np.std(arr1) == 0 or np.std(arr2) == 0:
            # If both are uniform, compare their means
            if np.std(arr1) == 0 and np.std(arr2) == 0:
                return abs(np.mean(arr1) - np.mean(arr2)) < 10
            return False
        
        # Calculate correlation with np.corrcoef
        correlation = np.corrcoef(arr1.flatten(), arr2.flatten())[0,1]
        return False if np.isnan(correlation) else correlation > threshold
        
    except Exception as e:
        print(f"Warning: Error comparing images: {e}")
        return False

def extract_pdf_to_latex_project(pdf_path, output_dir):
    """
    Extract PDF content into a compilable LaTeX project
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save LaTeX project
    """
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Create project structure
    project_dir = os.path.join(output_dir, f"{pdf_name}_latex")
    images_dir = os.path.join(project_dir, "images")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # Initialize result tracking
    result = {
        'text': [],
        'images': [],
        'tables': []
    }
    
    # Extract images and get their dimensions
    doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc[page_num]
        
        # First, save the full page image as a reference
        zoom = 2  # Adjust based on needed quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        page_image = f"page_{page_num + 1}.png"
        page_image_path = os.path.join(images_dir, page_image)
        pix.save(page_image_path)
        
        # Extract embedded images
        image_list = page.get_images()
        
        # Create a mask to track covered areas
        page_covered = False
        
        # Save each embedded image on the page
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            image_filename = f"image_p{page_num + 1}_{img_idx + 1}.{ext}"
            image_path = os.path.join(images_dir, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            # Add image reference to result
            result['images'].append({
                'path': f"images/{image_filename}",
                'page': page_num,
                'width': base_image["width"],
                'height': base_image["height"]
            })
            
            # Compare extracted image with the page image
            if os.path.exists(image_path) and os.path.exists(page_image_path):
                if images_are_similar(image_path, page_image_path):
                    page_covered = True
                    break
        
        # If page isn't covered by extracted images, keep the page image
        if not page_covered:
            result['images'].append({
                'path': f"images/{page_image}",
                'page': page_num,
                'is_page': True
            })
        else:
            os.remove(page_image_path)
    
    # Extract text and tables with pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract text
            text = page.extract_text()
            if text:
                result['text'].append({
                    'content': text,
                    'page': page_num
                })
            
            # Extract tables
            tables = page.extract_tables()
            if tables:
                for table_idx, table in enumerate(tables):
                    result['tables'].append({
                        'content': table,
                        'page': page_num,
                        'index': table_idx
                    })
    
    # Generate main.tex file
    latex_content = [
        "\\documentclass{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{graphicx}",
        "\\usepackage{float}",
        "\\usepackage{booktabs}",
        "\\usepackage{longtable}",
        "\\usepackage{amsmath}",
        "\\usepackage{amssymb}",
        "\\graphicspath{{./images/}}",
        "",
        "\\begin{document}",
        ""
    ]
    
    # Combine content in page order
    for page_num in range(doc.page_count):
        # Add text
        page_text = next((item['content'] for item in result['text'] 
                         if item['page'] == page_num), None)
        if page_text:
            latex_content.append(page_text)
            latex_content.append("")
        
        # Add tables
        page_tables = [table for table in result['tables'] 
                      if table['page'] == page_num]
        for table in page_tables:
            latex_table = convert_table_to_latex(table['content'])
            latex_content.append("\\begin{table}[H]")
            latex_content.append("\\centering")
            latex_content.append(latex_table)
            latex_content.append("\\caption{Table}")
            latex_content.append("\\end{table}")
            latex_content.append("")
        
        # Add images
        page_images = [img for img in result['images'] 
                      if img['page'] == page_num and not img.get('is_page')]
        for img in page_images:
            latex_content.append("\\begin{figure}[H]")
            latex_content.append("\\centering")
            
            # For small images, use their natural size instead of scaling to page width
            if img.get('width') and img.get('height') and img['width'] < 100:
                latex_content.append(f"\\includegraphics{{{img['path']}}}")
            else:
                latex_content.append(f"\\includegraphics[width=0.8\\textwidth]{{{img['path']}}}")
                
            latex_content.append("\\caption{Figure}")
            latex_content.append("\\end{figure}")
            latex_content.append("")
    
    latex_content.append("\\end{document}")
    
    # Save main.tex
    main_tex_path = os.path.join(project_dir, "main.tex")
    with open(main_tex_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_content))
    
    # Create build script
    if os.name == 'nt':  # Windows
        with open(os.path.join(project_dir, "build.bat"), 'w') as f:
            f.write("pdflatex main.tex\n")
    else:  # Unix-like
        with open(os.path.join(project_dir, "build.sh"), 'w') as f:
            f.write("#!/bin/bash\npdflatex main.tex\n")
        os.chmod(os.path.join(project_dir, "build.sh"), 0o755)
    
    doc.close()
    return project_dir

def convert_table_to_latex(table):
    """Convert a table array to LaTeX tabular environment"""
    if not table:
        return ""
    
    num_cols = len(table[0])
    latex_lines = [
        "\\begin{tabular}{" + "c" * num_cols + "}",
        "\\toprule"
    ]
    
    for i, row in enumerate(table):
        latex_lines.append(" & ".join(str(cell) for cell in row) + " \\\\")
        if i == 0:  # After header
            latex_lines.append("\\midrule")
    
    latex_lines.extend([
        "\\bottomrule",
        "\\end{tabular}"
    ])
    
    return "\n".join(latex_lines)

def process_pdf_directory(input_dir, output_dir):
    """Process all PDFs in a directory and create LaTeX projects"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    error_count = 0
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        try:
            project_dir = extract_pdf_to_latex_project(pdf_path, output_dir)
            print(f"Created LaTeX project for {pdf_file} in {project_dir}")
        except Exception as e:
            error_count += 1
            print(f"Error processing {pdf_file}: {str(e)}")
    
    print(f"\nProcessing complete. Total errors: {error_count}")
    return error_count

if __name__ == "__main__":
    input_dir = "../"
    output_dir = "../latex_projects"
    
    total_errors = process_pdf_directory(input_dir, output_dir)
    print(f"Total errors across all PDFs: {total_errors}")