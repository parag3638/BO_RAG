import pdfplumber
import re
import warnings
import logging
import pandas as pd

# === Suppress PDFMiner CropBox warnings ===
warnings.filterwarnings("ignore")
logging.getLogger("pdfminer").setLevel(logging.ERROR)

pdf_path = "Blood_Report.pdf"
all_text = ""
name, age, gender = "Unknown", "Unknown", "Unknown"

# === STEP 1: Open PDF once to extract header info and full text ===
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue

        # Extract header info only from the first page
        if i == 0:
            name_match = re.search(r"Name\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
            age_match = re.search(r"Age\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
            gender_match = re.search(r"Gender\s*[:\-]?\s*(Male|Female|Other)", text, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
            if age_match:
                age = age_match.group(1).strip()
            if gender_match:
                gender = gender_match.group(1).strip()

        # Append each page's text with a page marker
        all_text += f"\n--- Page {i + 1} ---\n{text}"

# Print header info
print(f"👤 Name: {name}")
print(f"🎂 Age: {age}")
print(f"⚧️ Gender: {gender}")

# === STEP 2: Clean up unwanted lines from the full text ===
cleaned_lines = []
for line in all_text.splitlines():
    line = line.strip()
    # Remove page header/footer lines
    if re.match(r"^Page\s+\d+\s+of\s+\d+$", line):
        continue
    # Remove lines that are likely lab numbers or IDs (e.g., *473137934*)
    if re.match(r"^\*?\d{9}\*?$", line):
        continue
    # Skip lines starting with patient info or lab address details
    if line.startswith("Name :") or line.startswith("Lab No.") or "Modern Pathology Lab" in line:
        continue
    cleaned_lines.append(line)

# === STEP 3: Use a regex to extract test result rows ===
pattern = re.compile(r"""
    ^(.+?)                     # Test Name (non-greedy)
    \s+([0-9.]+)               # Value (numbers with decimals)
    \s+([a-zA-Z/%μgndL.]+)      # Unit (letters, /, %, μ, etc.)
    \s+([<>=.\d\s\-]+[a-zA-Z/%μgndL.]*)?$  # Reference Range (optional)
""", re.VERBOSE)

results = []
for line in cleaned_lines:
    match = pattern.match(line)
    if match:
        test = match.group(1).strip()
        value = match.group(2).strip()
        unit = match.group(3).strip()
        ref = match.group(4).strip() if match.group(4) else ""
        results.append({
            "Test Name": test,
            "Value": value,
            "Unit": unit,
            "Reference Range": ref
        })

# === STEP 4: Convert parsed results to a DataFrame and display it ===
df = pd.DataFrame(results)
print("\nStructured Lab Results:")
print(df)

# === Optional: Save the full parsed text and structured results ===
with open("parsed_lab_report.txt", "w", encoding="utf-8") as f:
    f.write(all_text)
