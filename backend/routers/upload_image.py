from fastapi import APIRouter
from fastapi import Form, UploadFile, HTTPException, Request, File
from globals import logger_manager, config, main_logger
from typing import Any
from core.database.db_manager import get_database
from pathlib import Path
import os
import shutil
from uuid import uuid4
from fastapi.responses import JSONResponse


router = APIRouter()

# This API is used when the user clicks on join call button. It captures the user's image and saves it to the static folder.
@router.post("/upload_image/")
async def upload_image(
    user_id: str = Form(...),                    # Unique user/session ID
    image: UploadFile = File(...)
):
    main_logger.info(f"Uploading image for user: {user_id}")
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Only JPEG/PNG supported.")
    
    upload_dir = "static/"+user_id+"/images"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        main_logger.info(f"Created directory: {upload_dir}")
    else:
        # delete and recreate the directory
        shutil.rmtree(upload_dir)
        os.makedirs(upload_dir)
        main_logger.info(f"Directory already exists so recreated: {upload_dir}")
    # Generate a safe filename
    file_ext = image.filename.split(".")[-1]
    filename = f"{user_id}_{uuid4().hex}.{file_ext}"
    filepath = os.path.join(upload_dir, filename)
    main_logger.info(f"Saving image to {filepath}")
    # Save the file
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return JSONResponse(content={"message": "Image uploaded successfully", "filename": filename})