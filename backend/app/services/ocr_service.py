"""Receipt OCR service using MinIO (S3-compatible) and Tesseract"""
from __future__ import annotations

import io
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Any

from PIL import Image
import pytesseract
import boto3

from app.config import settings


@dataclass
class ReceiptParseResult:
    text: str
    merchant: Optional[str]
    total_amount: Optional[float]
    date: Optional[str]
    s3_key: Optional[str]
    s3_url: Optional[str]


def _get_s3_client():
    protocol = "https" if settings.MINIO_SECURE else "http"
    endpoint = f"{protocol}://{settings.MINIO_ENDPOINT}"
    return boto3.client(
        "s3",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        endpoint_url=endpoint,
    )


def ensure_bucket_exists() -> None:
    s3 = _get_s3_client()
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if settings.MINIO_BUCKET not in buckets:
        s3.create_bucket(Bucket=settings.MINIO_BUCKET)


def upload_receipt(image_bytes: bytes, content_type: str) -> str:
    ensure_bucket_exists()
    s3 = _get_s3_client()
    key = f"receipts/{uuid.uuid4()}.png"
    s3.put_object(Bucket=settings.MINIO_BUCKET, Key=key, Body=image_bytes, ContentType=content_type)
    return key


def public_url_for(key: str) -> str:
    protocol = "https" if settings.MINIO_SECURE else "http"
    return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{key}"


def ocr_image(image_bytes: bytes) -> str:
    with Image.open(io.BytesIO(image_bytes)) as img:
        return pytesseract.image_to_string(img)


def parse_receipt_text(text: str) -> Dict[str, Any]:
    # Very naive parsing; real implementation should use regexes/NER
    import re

    amount = None
    match_amount = re.search(r"(?:TOTAL|Amount)\s*\$?([0-9]+(?:\.[0-9]{2})?)", text, re.IGNORECASE)
    if match_amount:
        try:
            amount = float(match_amount.group(1))
        except Exception:
            amount = None

    date = None
    match_date = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{2,4})", text)
    if match_date:
        date = match_date.group(1)

    merchant = None
    first_line = text.strip().splitlines()[0] if text.strip().splitlines() else None
    if first_line and len(first_line) <= 64:
        merchant = first_line.strip()

    return {"merchant": merchant, "total_amount": amount, "date": date}


def process_receipt(image_bytes: bytes, content_type: str) -> ReceiptParseResult:
    key = upload_receipt(image_bytes, content_type)
    text = ocr_image(image_bytes)
    parsed = parse_receipt_text(text)
    return ReceiptParseResult(
        text=text,
        merchant=parsed.get("merchant"),
        total_amount=parsed.get("total_amount"),
        date=parsed.get("date"),
        s3_key=key,
        s3_url=public_url_for(key),
    )


