import re
import os
import uuid
import pytz
import time
import base64
import traceback
from io import BytesIO
from datetime import datetime
from PIL import Image
from fastapi import FastAPI, Form, status
from fastapi.responses import JSONResponse

from app.ocr import extract_text, get_reader

egypt_tz = pytz.timezone("Africa/Cairo")
app = FastAPI()

@app.on_event("startup")
def load_model():
    get_reader()


def get_image_size_mb(b64_string: str) -> float:
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    padding = b64_string.count("=")
    original_bytes = (len(b64_string) * 3) // 4 - padding
    size_mb = original_bytes / (1024 * 1024)
    return size_mb


base64_pattern = re.compile(r"^([A-Za-z0-9+/=]+\s*)*$")
def is_valid_base64(request_id, base64_str):
    if base64_str.startswith("data:"):
        try:
            base64_str = base64_str.split(",", 1)[1]
        except Exception as e:
            return {
                "id": request_id, "status": "error", "status_code": 422,
                "message": "Invalid base64", "data": {"id": request_id, "printed_score": ""}
            }
    if not base64_pattern.match(base64_str):
        return {
            "id": request_id, "status": "error", "status_code": 422,
            'message': "Invalid base64", "data": {"id": request_id, "printed_score": ""}
        }
    try:
        decoded_data = base64.b64decode(base64_str, validate=True)
        with Image.open(BytesIO(decoded_data)) as img:
            img.verify()
        return True
    except Exception as e:
        return {
            "id": request_id, "status": "error", "status_code": 422,
            'message': "Invalid base64", "data": {"id": request_id, "printed_score": ""}
        }


@app.post("/api/ai/v1.0.0/ocr")
def ocr_endpoint(id: str = Form(""), front_id: str = Form(""), back_id: str = Form("")):

    request_timestamp = datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S')
    start = time.time()

    result = main_execution(request_timestamp, start, id, front_id, back_id)
    if result['status_code'] == 422:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=result
        )
    
    elif result['status_code'] == 200:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
    
    elif result['status_code'] == 500:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=result
        )

def main_execution(request_timestamp, start, id, front_id, back_id):

    try:

        if not id or id.strip() == "":
            return {
                "id": id,
                "status_code": 422,
                "status": "error",
                "message": "id is required",
                "text": ""
            }
        if not front_id or front_id.strip() == "":
            return {
                "id": id,
                "status_code": 422,
                "status": "error",
                "message": "front_id is required",
                "text": ""
            }
        validation_result = is_valid_base64(id, front_id)
        if not isinstance(validation_result, bool):
            return {
                "id": id,
                "status_code": 422,
                "status": "error",
                "message": "Invalid base64 for front_id",
                "text": ""
            }
        if back_id:
            validation_result = is_valid_base64(id, back_id)
            if not isinstance(validation_result, bool):
                return {
                    "id": id,
                    "status_code": 422,
                    "status": "error",
                    "message": "Invalid base64 for back_id",
                    "text": ""
                }
        front_ai_start_time = -1
        front_ai_end_time = -1
        back_ai_start_time = -1
        back_ai_end_time = -1
        front_img_path = ""
        front_text = ""
        back_img_path = ""
        back_text = ""

        front_img_path = f"./{uuid.uuid4()}_{id}.png"
        with open(front_img_path, "wb") as f:
            f.write(base64.b64decode(front_id.split(",")[1]))

        front_ai_start_time = time.time()
        front_text = extract_text(front_img_path)
        front_ai_end_time = time.time()

        if back_id:
            back_img_path = f"./{uuid.uuid4()}_{id}.png"
            with open(back_img_path, "wb") as f:
                f.write(base64.b64decode(back_id.split(",")[1]))

            back_ai_start_time = time.time()
            back_text = extract_text(back_img_path)
            back_ai_end_time = time.time()

        print({
            "timestamp": request_timestamp,
            "request_id": id,
            "status_code": "200",
            "status": "success",
            "service_name": "ocr_id",
            "front_ai_response_time": front_ai_end_time - front_ai_start_time,
            "back_ai_response_time": back_ai_end_time - back_ai_start_time,
            "total_response_time": time.time() - start,
            "error_message": "",
            "traceback": "",
            "front_id_image_size": f"{get_image_size_mb(front_id)} MB" if front_id else -1,
            "back_id_image_size": f"{get_image_size_mb(back_id)} MB" if back_id else -1,
            "front_text": front_text,
            "back_text": back_text
        })

        if os.path.exists(front_img_path):
            os.remove(front_img_path)

        if os.path.exists(back_img_path):
            os.remove(back_img_path)

        return {
            "id": id,
            "status_code": 200,
            "status": "success",
            "front_text": front_text,
            "back_text": back_text
        }
    except Exception as e:
        print({
            "timestamp": request_timestamp,
            "request_id": id,
            "status_code": "500",
            "status": "error",
            "service_name": "ocr_id",
            "front_ai_response_time": -1,
            "back_ai_response_time": -1,
            "total_response_time": time.time() - start,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "front_id_image_size": f"{get_image_size_mb(front_id)} MB" if front_id else -1,
            "back_id_image_size": f"{get_image_size_mb(back_id)} MB" if back_id else -1,
            "front_text": front_text,
            "back_text": back_text
        })

        if os.path.exists(front_img_path):
            os.remove(front_img_path)

        if os.path.exists(back_img_path):
            os.remove(back_img_path)

        return {
            "id": id,
            "status_code": 500,
            "status": "error",
            "message": "failed to process the image",
            "front_text": "",
            "back_text": ""
        }



@app.get("/")
def health():
    return {"status": "Hello from OCR v1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}