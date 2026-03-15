import re

FILE_PATH = "transcript.md"

filler_patterns = [
    r"\bum\b",
    r"\buh\b",
    r"\blike\b",
    r"\byou know\b",
    r"\bactually\b",
    r"\bbasically\b",
    r"\bliterally\b",
    r"\bkinda\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bi mean\b",
    r"\bwell\b",
    r"\bso\b",
    r"\bright\b",
    r"\bokay\b",
    r"\bi think\b"
]

def remove_fillers(text):
    for pattern in filler_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # remove repeated words (e.g., "I I I think")
    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)
    text = re.sub(r' +', ' ', text)
    text = text.replace('.', '')

    return text.strip()

# 1. read transcript
with open(FILE_PATH, "r", encoding="utf-8") as f:
    transcript = f.read()

# 2. clean text
cleaned_text = remove_fillers(transcript)

# 3. overwrite file
with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(cleaned_text)



print("Transcript cleaned and overwritten.")