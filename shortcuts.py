# Search for the most recent OCR chunk
from typing import Optional
from utils.screenpipe_client import search
from utils.sp_utils import get_past_time
from utils.outputs import OCR


def get_most_recent_ocr_chunk(
        hours_ago: int = 1,
        save_frame: bool = True,
        image_output_path: str = "last_ocr_chunk.png"):
    """
    Fetches the most recent OCR chunk from the screenpipe server. By default, saves the image.

    Args:
    - days_ago (int): The earliest timestamp to search for OCR chunks. Defaults to 1 day ago.
    - save_frame (bool): If True, the frame will be saved to the specified path. Defaults to True.
    - image_output_path (str): The output path for the frame image. Defaults to "last_ocr_chunk.png".
    """
    results = search(
        content_type="ocr",
        limit=1,
        start_time=get_past_time(
            hours=hours_ago),
        include_frames=True)
    if results and results["data"]:
        ocr_chunk = OCR(**results["data"][0]["content"])
        print(f"Most recent OCR chunk found: {ocr_chunk}")
        if save_frame:
            ocr_chunk.save_frame(image_output_path)
        return ocr_chunk
    else:
        print("No OCR chunks found.")

# TODO: get_latest_ocr_chunks should have a minimum timestamp of 2 min
# since the most recent OCR chunk


def get_latest_ocr_chunks(
        limit: int = 15,
        min_length: int = 25,
        include_dupe: bool = False,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None):
    """
    Fetches the OCR chunks from the screenpipe server and returns a list of chunks,
    truncating the list upon encountering the first duplicate app name and window name unless include_dupe is True.

    Args:
    - limit (int): The maximum number of OCR chunks to fetch. Defaults to 20.
    - min_length (int): The minimum character count in OCR text chunks. Defaults to 25.
    - include_dupe (bool): If True, the list will include the duplicate app name and window name. Defaults to False.

    Returns:
    - List[OCR]: A list of OCR chunks, truncated at the first duplicate app name and window name if include_dupe is False.
    """
    results = search(
        content_type="ocr",
        limit=limit,
        min_length=min_length,
        start_time=start_time,
        end_time=end_time)
    if results and results["data"]:
        ocr_chunks = []
        seen_app_window_names = set()
        count = 0
        for result in results["data"]:
            count += 1
            ocr_chunk = OCR(**result["content"])
            app_window_name = (ocr_chunk.app_name, ocr_chunk.window_name)
            if app_window_name in seen_app_window_names:
                if include_dupe:
                    ocr_chunks.append(ocr_chunk)
                    print(f"Dupe@{count}: {app_window_name} (included)")
                else:
                    print(f"Dupe@{count}: {app_window_name}")
                    print("Truncating list.")
                    break
            else:
                seen_app_window_names.add(app_window_name)
                ocr_chunks.append(ocr_chunk)
        if ocr_chunks:
            print(f"{len(ocr_chunks)} OCR chunks found: {ocr_chunks}")
            return ocr_chunks
    print("No OCR chunks found.")
    return []


def main():
    get_most_recent_ocr_chunk()


if __name__ == "__main__":
    main()
