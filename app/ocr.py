import easyocr

LANGUAGES = ["ar", "en"]

#! singleton pattern for easyocr.Reader
_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(LANGUAGES)
    return _reader


def extract_text(image_path: str) -> str:
    reader = get_reader()
    results = reader.readtext(image_path, detail=0)

    return "\n".join(results) if results else ""
