from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from globals import main_logger

from core.database.db_manager import get_database

router = APIRouter()


@router.post("/upload_video_chunk")
async def upload_video_chunk_api(
    user_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    video: UploadFile = Form(...),
):
    try:
        return await upload_video_chunk(user_id, chunk_index, total_chunks, video)
    except Exception as e:
        print("Video chunk upload failed:", e)
        raise HTTPException(status_code=500, detail="Failed to upload video chunk")


async def upload_video_chunk(
    user_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    video: UploadFile = Form(...),
):
    try:
        database = await get_database(main_logger)
        firebase_user_id = await database.get_user_id_by_email(user_id)
        if firebase_user_id is None:
            raise HTTPException(status_code=404, detail="User not found")
        latest_session = await database.get_most_recent_session_id_by_user_id(firebase_user_id)

        # Step 1: Save to disk
        upload_dir = Path("static") / user_id / "videos"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # we should create directory for session within upload_dir
        session_dir = upload_dir / latest_session if latest_session else upload_dir
        session_dir.mkdir(parents=True, exist_ok=True)

        local_path = session_dir / video.filename
        content = await video.read()

        with open(local_path, "wb") as f:
            f.write(content)

        main_logger.info(f"Saved chunk {chunk_index + 1}/{total_chunks}: {local_path}")

        # Step 2: Upload to Firebase
        await database.upload_video(
            firebase_user_id, latest_session, video.filename, content, video.content_type
        )

        return {
            "status": "success",
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "filename": video.filename,
        }

    except Exception as e:
        main_logger.error(f"Upload failed: {e}")
        return {"status": "error", "message": str(e)}
