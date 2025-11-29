import glob
import re
import string

import chromadb
import pdfplumber
import PyPDF2
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import LongformerTokenizer

tokenizer = LongformerTokenizer.from_pretrained("allenai/longformer-base-4096")
# model = LongformerModel.from_pretrained('allenai/longformer-base-4096')
sentence_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")


class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        # embed the documents
        embedding_list = []
        for data in input:
            embeddings = sentence_model.encode(data)
            embedding_list.append(embeddings.tolist())

        return embedding_list


def remove_headers_footers(text):
    lines = text.split("\n")
    filtered_lines = lines[2:-2]  # Skip first 2 and last 2 lines as an example
    return "\n".join(filtered_lines)


def remove_page_numbers(text):
    return re.sub(r"\b\d+\b", "", text)


def remove_extra_spaces(text):
    return re.sub(r"\s+", " ", text)


def clean_text(text):
    text = re.sub(r"[^\w\s]", "", text)  # removing special characters
    return text.strip()


def remove_index_lines(text):
    lines = text.split("\n")
    cleaned_lines = [line for line in lines if "....." not in line]
    return "\n".join(cleaned_lines)


def merge_hyphen_lines(text):
    lines = text.split("\n")
    merged_lines = []
    for line in lines:
        # If the line ends with hyphen, merge it with the next line (if there is one)
        if line.endswith("-") and len(merged_lines) > 0:
            merged_lines[-1] = merged_lines[-1] + line[:-1]  # remove the hyphen and merge
        else:
            merged_lines.append(line)
    return "\n".join(merged_lines)


def remove_short_lines(text, min_length):
    lines = text.split("\n")
    long_lines = [line for line in lines if len(line.strip().split()) >= min_length]
    return "\n".join(long_lines)


def extract_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in tqdm(enumerate(pdf.pages)):
            # text += page.extract_text()
            pages.append(page.extract_text())
            # if index > 20:
            #    break
    return pages


def parse_contents(contents_data):
    # Define regex patterns
    chapter_pattern = re.compile(r"^(\d+)\s+(.+?)\s+(\d+)$")  # Matches chapter titles
    subtopic_pattern = re.compile(r"^(\d+(\.\d+)+)\s+(.+?)\s+\.+\s+(\d+)$")  # Matches subtopics

    chapters = []
    current_chapter = None

    for page in contents_data:
        page = page.strip()
        lines = page.split("\n")  # Split page into lines

        for line in lines:
            line = line.strip()
            # print("Processing line:", repr(line))

            # Match chapters
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                # print("Chapter match found:", line)
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    "chapter_number": chapter_match.group(1),
                    "title": chapter_match.group(2).strip(),
                    "start_page": int(chapter_match.group(3)),
                    "subtopics": [],
                }
                continue

            # Match subtopics
            subtopic_match = subtopic_pattern.match(line)
            if subtopic_match and current_chapter:
                # print("Subtopic match found:", line)
                subtopic = {
                    "title": subtopic_match.group(3).strip(),
                    "page": int(subtopic_match.group(4)),
                }
                current_chapter["subtopics"].append(subtopic)
            # elif not subtopic_match:
            #    print("Subtopic not matched:", repr(line))

    # Append the last chapter
    if current_chapter:
        chapters.append(current_chapter)

    return chapters


def parse_new_contents(contents_data):
    # Define patterns
    chapter_pattern = re.compile(r"^(Chapter\s+\d+)\s+(.+)$")  # Matches "Chapter 1 Introduction"
    subtopic_pattern = re.compile(
        r"^(\d+(\.\d+)+)\s+(.+?)\s+(\d+)$"
    )  # Matches subtopics with numbers and pages
    merged_line_pattern = re.compile(
        r"(\d+(\.\d+)+\s+.+?\s+\d+)"
    )  # Matches merged subtopics in a line

    chapters = []
    current_chapter = None

    for page in contents_data:
        page = page.strip()
        lines = page.split("\n")  # Split page into lines

        for line in lines:
            line = line.strip()
            print("Processing line:", repr(line))

            # Normalize the line
            line = line.replace("\u00a0", " ")  # Replace non-breaking spaces
            line = re.sub(r"\s+", " ", line)  # Normalize whitespace

            # Ignore headers like "Contents"
            if line.lower() == "contents":
                print("Skipping header:", line)
                continue

            # Match chapters
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                # print("Chapter match found:", line)
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    "chapter_number": chapter_match.group(1),
                    "title": chapter_match.group(2).strip(),
                    "subtopics": [],
                }
                continue

            # Match subtopics
            subtopic_match = subtopic_pattern.match(line)
            if subtopic_match and current_chapter:
                print("Subtopic match found:", line)
                subtopic = {
                    "title": subtopic_match.group(3).strip(),
                    "page": int(subtopic_match.group(4)),
                }
                current_chapter["subtopics"].append(subtopic)
                continue

            # Handle merged lines
            merged_matches = merged_line_pattern.findall(line)
            if merged_matches and current_chapter:
                print("Merged line found:", line)
                for match in merged_matches:
                    subtopic_parts = subtopic_pattern.match(match[0])
                    if subtopic_parts:
                        subtopic = {
                            "title": subtopic_parts.group(3).strip(),
                            "page": int(subtopic_parts.group(4)),
                        }
                        current_chapter["subtopics"].append(subtopic)
                continue

            # Log unmatched lines for debugging
            print("Unmatched line:", repr(line))

    # Append the last chapter
    if current_chapter:
        chapters.append(current_chapter)

    return chapters


def parse_contents_v2(contents_data):
    # Define patterns
    chapter_pattern = re.compile(r"^(Chapter\s+\d+):?\s+(.+?)\s+(\d+)")
    subtopic_pattern = re.compile(r"^(Section\s+\d+(\.\d+)*):?\s+(.+?)\s+(\d+)")

    chapters = []
    current_chapter = None

    for page in contents_data:
        page = page.strip()
        lines = page.split("\n")  # Split page into lines

        for line in lines:
            line = line.strip()
            print("Processing line:", repr(line))

            # Normalize line
            line = re.sub(r"\s+", " ", line)

            # Match chapters
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                print("Chapter match found:", line)
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    "chapter_number": chapter_match.group(1),
                    "title": chapter_match.group(2).strip(),
                    "start_page": int(chapter_match.group(3)),
                    "subtopics": [],
                }
                continue

            # Match subtopics
            subtopic_match = subtopic_pattern.match(line)
            if subtopic_match and current_chapter:
                print("Subtopic match found:", line)
                subtopic = {
                    "title": subtopic_match.group(3).strip(),
                    "page": int(subtopic_match.group(4)),
                }
                current_chapter["subtopics"].append(subtopic)
                continue

            # Log unmatched lines for debugging
            print("Unmatched line:", repr(line))

    # Append the last chapter
    if current_chapter:
        chapters.append(current_chapter)

    return chapters


def extract_text_from_pdf(file_path):
    pdf_file_obj = open(file_path, "rb")
    pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
    num_pages = len(pdf_reader.pages)
    print("Number of pages", num_pages)
    full_text = ""
    for page in range(num_pages):
        page_obj = pdf_reader.pages[page]
        full_text += page_obj.extract_text()

    pdf_file_obj.close()
    # Replace consecutive whitespaces with a single whitespace
    allowed_chars = string.ascii_letters + string.digits + string.punctuation + " " + "\n"
    pattern = "[^" + re.escape(allowed_chars) + "]"
    full_text = re.sub(pattern, "", full_text)
    # full_text = re.sub(r"[^a-zA-Z0-9\s]", "", full_text)
    # full_text = re.sub(r"^\..*", "", full_text, flags=re.MULTILINE)
    cleaned_content = remove_index_lines(full_text)
    merged_content = merge_hyphen_lines(cleaned_content)
    long_lines = remove_short_lines(merged_content, 5)
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(long_lines)

    return long_lines


def extract_potential_contents(file_path, max_pages=10):
    pdf_reader = PyPDF2.PdfReader(file_path)
    num_pages = len(pdf_reader.pages)
    contents_pages = []
    print("Number of pages", num_pages)
    for page_number in range(min(max_pages, num_pages)):
        page_obj = pdf_reader.pages[page_number]
        page_text = page_obj.extract_text()
        # print ("Page number:", page_number)
        # print (page_text)
        # if page_number > 5:
        #    print (page_text)
        # Look for patterns typical in contents pages
        if re.search(r"\bContents\b", page_text, re.IGNORECASE):
            contents_pages.append(page_text)

    return contents_pages


def calculate_page_ranges(chapters, total_pages):
    page_ranges = []
    for i in range(len(chapters)):
        start_page = chapters[i]["start_page"]
        end_page = chapters[i + 1]["start_page"] - 1 if i + 1 < len(chapters) else total_pages
        page_ranges.append(
            {
                "chapter_title": chapters[i]["title"],
                "start_page": start_page,
                "end_page": end_page,
                "subtopics": chapters[i]["subtopics"],
            }
        )
    return page_ranges


if __name__ == "__main__":
    persist_directory = "database/ml_chroma_db"  # Specify your desired directory
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    custom_embeddings = MyEmbeddingFunction()
    is_collection_present = False

    try:
        collection = chroma_client.get_collection("MachineLearning")
        print("Collection exists")
        is_collection_present = True
    except:
        print("Creating collection")
        is_collection_present = False
        # collection = chroma_client.create_collection(name='MachineLearning', embedding_function=custom_embeddings, metadata={"hnsw:space": "cosine"})

    if not is_collection_present:
        books = glob.glob("books/machine_learning/*.pdf")
        for file_path in books:
            print("Processing file:", file_path)
            # raw_text_list = extract_text("books/ML.pdf")
            potential_contents = extract_potential_contents(file_path)
            # print (potential_contents)
            parsed_contents = parse_contents(potential_contents)
            if len(parsed_contents) == 0:
                parsed_contents = parse_new_contents(potential_contents)
                if len(parsed_contents) == 0:
                    parsed_contents = parse_contents_v2(potential_contents)
            for chapter in parsed_contents:
                print(chapter.keys())

            """
            cleaned_paragraphs = []
            for raw_text in tqdm(raw_text_list):
                cleaned_text = remove_headers_footers(raw_text)
                cleaned_text = remove_page_numbers(cleaned_text)
                cleaned_text = remove_extra_spaces(cleaned_text)
                paragraphs = cleaned_text.split('\n\n')
                paragraphs = [clean_text(para) for para in paragraphs if len(clean_text(para)) > 5]

                for para in paragraphs:
                    tokens = tokenizer.tokenize(para)
                    input_ids = tokenizer.convert_tokens_to_ids(tokens)
                    for i in range(0, len(input_ids), 64):
                        chunk = input_ids[i:i + 64]
                        data = tokenizer.decode(chunk)
                        cleaned_paragraphs.append(data)

            print ("Number of paragraphs:", len(cleaned_paragraphs))
                    
            document_ids = list(map(lambda tup: f"id{tup[0]}", enumerate(cleaned_paragraphs)))
            collection.add(documents=cleaned_paragraphs, ids=document_ids)
            """
    # result = collection.query(query_texts=["what are the contents of the book?"], n_results=5, include=["documents", 'distances',])
    # print (result)
