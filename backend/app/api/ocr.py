"""OCR API endpoints"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.services.ocr_service import process_receipt
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router.post("/receipt")
async def upload_receipt(file: UploadFile = File(...), user=Depends(get_current_user)):
    if file.content_type not in ("image/png", "image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    image_bytes = await file.read()
    result = process_receipt(image_bytes, file.content_type)
    return JSONResponse(
        {
            "merchant": result.merchant,
            "total_amount": result.total_amount,
            "date": result.date,
            "text": result.text,
            "s3_key": result.s3_key,
            "s3_url": result.s3_url,
        }
    )


