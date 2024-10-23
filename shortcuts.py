# Search for the most recent OCR chunk
from utils.screenpipe_client import search
from utils.sp_utils import get_past_time
from utils.outputs import OCR
def get_most_recent_ocr_chunk(days_ago: int = 1, save_frame: bool = True, image_output_path: str = "last_ocr_chunk.png"):
    """Search for the most recent OCR chunk.

    Args:
    - days_ago (int): The earliest timestamp to search for OCR chunks. Defaults to 1 day ago.
    """
    results = search(content_type="ocr", limit=1, start_time=get_past_time(days_ago), include_frames=True)
    if results and results["data"]:
        ocr_chunk = OCR(**results["data"][0]["content"])
        print(f"Most recent OCR chunk found: {ocr_chunk}")

        #TODO: Error handling
        ocr_chunk.save_frame(image_output_path)

    else:
        print("No OCR chunks found.")
        return None

def main():
    get_most_recent_ocr_chunk()

if __name__ == "__main__":
    main()
