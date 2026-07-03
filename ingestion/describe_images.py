import base64
import io
import json
import os
import time
from PIL import Image
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

IMAGE_DIR = "data/pdfs/images"
OUTPUT_DIR = "data/pdfs/image_descriptions.json"
DELAY_SECS = 4.5

USE_GROQ = os.environ.get("GROQ", "").lower() == "true"

GEMINI_MODEL_NAME = "gemini-2.5-flash"
GROQ_MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

if USE_GROQ:
    from groq import Groq
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    from google import genai
    from google.genai import types
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


VISION_PROMPT = """This image is a page from an oral cancer research paper.

First, determine if this page contains a meaningful figure (histopathology image,
clinical photograph, CT/MRI scan, chart, graph, or diagram) or if it is mostly
text, a publisher watermark, blank space, or decorative content.

If it IS a meaningful figure, describe it using this structure:
- Image type: (histopathology / clinical photograph / medical imaging / chart or graph / molecular diagram / other)
- Key findings: what is visible, using precise medical terminology
- Clinical relevance: what this image demonstrates about oral cancer

If it is NOT a meaningful figure (mostly text, watermark, blank, or decorative),
respond with exactly: "NOT_A_FIGURE"

Be concise but specific. Use medical terminology where applicable."""


def get_all_images() -> list[dict]:
    images = []
    for paper_id in os.listdir(IMAGE_DIR):
        paper_dir = os.path.join(IMAGE_DIR, paper_id)
        if not os.path.isdir(paper_dir):
            continue
        for filename in os.listdir(paper_dir):
            if filename.endswith(".png"):
                images.append({
                    "paper_id": paper_id,
                    "filename": filename,
                    "path": os.path.join(paper_dir, filename),
                })
    return images


def _image_to_base64(image_path: str) -> str:
    with Image.open(image_path) as img:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")


def describe_with_groq(image_path: str) -> str:
    b64 = _image_to_base64(image_path)
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ],
        temperature=0.1,
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()


def describe_with_gemini(image_path: str) -> str:
    img = Image.open(image_path)
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=[VISION_PROMPT, img],
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=400,
        ),
    )
    return response.text.strip()


def describe_image(image_path: str) -> str | None:
    max_retries = 3

    for attempt in range(max_retries):
        try:
            text = describe_with_groq(image_path) if USE_GROQ else describe_with_gemini(image_path)

            # Clear negative — model confirmed not a figure
            if text == "NOT_A_FIGURE" or "NOT_A_FIGURE" in text[:30]:
                return None

            # Clear positive — got a real description
            if text and len(text.strip()) > 20:
                return text

            # Undefined — response exists but empty or too short
            # Could be a model hiccup, retry
            logger.warning(f"Undefined response (attempt {attempt+1}/{max_retries}) — retrying")
            time.sleep(10)
            continue

        except Exception as e:
            error_str = str(e)

            # Temporary server issues — retry
            if any(code in error_str for code in ["503", "429", "UNAVAILABLE", "rate_limit"]):
                wait = (attempt + 1) * 15
                logger.warning(f"Temporary error (attempt {attempt+1}/{max_retries}). Waiting {wait}s...")
                time.sleep(wait)
                continue

            # Permanent error — skip
            logger.error(f"[FAIL] permanent error: {e}")
            return None

    # All retries exhausted — status is truly undefined, skip for now
    logger.warning(f"Undefined after {max_retries} attempts — skipping {image_path}")
    return None


def main():
    try:
        images = get_all_images()
        results = []
        described = 0
        skipped = 0
        failed = 0
        existing_paths = set()

        provider = "Groq" if USE_GROQ else "Gemini"
        logger.info(f"Using provider: {provider}")

        if os.path.exists(OUTPUT_DIR):
            with open(OUTPUT_DIR, "r", encoding="utf-8") as f:
                results = json.load(f)
            existing_paths = {r["path"] for r in results}
            logger.info(f"Loaded {len(existing_paths)} existing image descriptions.")

        for i, img in enumerate(images, 1):
            if img["path"] in existing_paths:
                continue

            logger.info(f"[{i}/{len(images)}] {img['paper_id'][:20]}... / {img['filename']}")

            description = describe_image(img["path"])

            if description:
                results.append({
                    "paper_id":    img["paper_id"],
                    "filename":    img["filename"],
                    "path":        img["path"],
                    "description": description,
                })
                described += 1
                logger.info("[OK] Described")
            else:
                skipped += 1
                logger.info("[SKIP] Not a meaningful figure")

            if i % 10 == 0:
                with open(OUTPUT_DIR, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

            time.sleep(DELAY_SECS)

        with open(OUTPUT_DIR, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info("=" * 50)
        logger.info(f"Described: {described}")
        logger.info(f"Skipped (not figures): {skipped}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Saved to: {OUTPUT_DIR}")

    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()
