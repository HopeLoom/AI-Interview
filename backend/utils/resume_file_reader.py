import pdfplumber
from docx import Document


def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


def extract_text_from_docx(file_path):
    """Extract text from Word Document using python-docx."""
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def parse_resume(file_path):
    """Main function to parse resume and extract information."""
    # Extract text based on file type
    if file_path.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please use .pdf or .docx.")
    """
    print (text)
    # Extract key fields using NLP and regex
    basic_fields = extract_basic_fields(text)

    # Parse full resume using PyResparser (optional, adds extra details)
    try:
        detailed_fields = ResumeParser(file_path).get_extracted_data()
    except Exception as e:
        detailed_fields = {}

    # Combine results
    final_fields = {**basic_fields, **detailed_fields}
    return final_fields
    """
    return text


# Example Usage
if __name__ == "__main__":
    file_path = "example_resume.pdf"  # Replace with your resume file path
    extracted_data = parse_resume(file_path)
    if isinstance(extracted_data, dict):
        for field, value in extracted_data.items():
            print(f"{field}: {value}")
    else:
        print(f"Extracted text: {extracted_data}")
