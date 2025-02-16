from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from integrations.close.client import CloseClient, CloseAPIError
from main import CallProcessor
from config.settings import CLOSE_API_KEY, CLOSE_WEBHOOK_SECRET
from .monitoring import ERROR_COUNT, PROCESSING_TIME

logger = logging.getLogger(__name__)
router = APIRouter()

async def process_call_async(call_data: Dict[str, Any]):
    """Process call in background task"""
    try:
        processor = CallProcessor()
        start_time = datetime.now()
        
        result = processor.process_call(
            transcript=call_data["transcript"],
            call_metadata=call_data
        )
        
        # Record processing time
        duration = (datetime.now() - start_time).total_seconds()
        PROCESSING_TIME.labels(
            method="POST",
            endpoint="/webhook/close/call-completed"
        ).observe(duration)
        
        logger.info(f"Successfully processed call {call_data['call_id']} in background")
        
    except Exception as e:
        logger.error(f"Error in background processing of call {call_data['call_id']}: {str(e)}")
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()

@router.post("/webhook/close/call-completed")
async def handle_call_completed(
    request: Request,
    background_tasks: BackgroundTasks,
    x_close_signature: Optional[str] = Header(None)
):
    """
    Handle call completion webhook from Close
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        x_close_signature: Close webhook signature
        
    Returns:
        Dict containing status and call ID
        
    Raises:
        HTTPException: If webhook processing fails
    """
    try:
        # Get the raw payload
        payload = await request.json()
        
        # Initialize Close client
        close = CloseClient(CLOSE_API_KEY, CLOSE_WEBHOOK_SECRET)
        
        # Verify webhook signature if provided
        if x_close_signature:
            if not close.verify_webhook(payload, x_close_signature):
                logger.error("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Extract call details
        call_data = {
            "call_id": payload.get("data", {}).get("id"),
            "lead_id": payload.get("data", {}).get("lead_id"),
            "user_id": payload.get("data", {}).get("user_id"),
            "direction": payload.get("data", {}).get("direction"),
            "duration": payload.get("data", {}).get("duration"),
            "status": payload.get("data", {}).get("status")
        }
        
        # Validate required fields
        if not all([call_data["call_id"], call_data["lead_id"], call_data["user_id"]]):
            raise ValueError("Missing required fields in webhook payload")
        
        # Log the webhook receipt
        logger.info(f"Received call completion webhook for call {call_data['call_id']}")
        
        # Get full call details including transcript
        call_details = close.get_call(call_data["call_id"])
        call_data["transcript"] = call_details.get("recording_transcript", {}).get("summary_text", "")
        
        # Add call processing to background tasks
        background_tasks.add_task(process_call_async, call_data)
        
        return {
            "status": "success",
            "message": "Webhook received and processing initiated",
            "call_id": call_data["call_id"],
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        ERROR_COUNT.labels(error_type="ValueError").inc()
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error processing Close webhook: {str(e)}", exc_info=True)
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=str(e))