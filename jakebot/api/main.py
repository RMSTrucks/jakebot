from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette_prometheus import PrometheusMiddleware, metrics
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import logging
from datetime import datetime

from main import CallProcessor
from .monitoring import MetricsMiddleware, COMMITMENT_COUNT, TASK_CREATION, ERROR_COUNT
from .routes import close_webhooks

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="JakeBot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)

# Include Close webhook routes
app.include_router(close_webhooks.router, tags=["webhooks"])

class CallData(BaseModel):
    lead_id: str
    user_id: str
    user_name: str
    call_id: str
    transcript: str
    duration: int = None
    direction: str = None
    disposition: str = None

    class Config:
        schema_extra = {
            "example": {
                "lead_id": "lead_123",
                "user_id": "user_456",
                "user_name": "John Agent",
                "call_id": "call_789",
                "transcript": "Agent: I will send the documents tomorrow.",
                "duration": 300,
                "direction": "outbound",
                "disposition": "completed"
            }
        }

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and their processing time"""
    start_time = datetime.now()
    response = await call_next(request)
    duration = (datetime.now() - start_time).total_seconds()
    
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {duration}s"
    )
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/process-call")
async def process_call(call_data: CallData):
    """
    Process a call transcript and create tasks
    
    Args:
        call_data: Call data including transcript and metadata
    
    Returns:
        JSON response indicating success or failure
    
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Processing call {call_data.call_id} for lead {call_data.lead_id}")
        
        processor = CallProcessor()
        result = processor.process_call(
            transcript=call_data.transcript,
            call_metadata={
                "lead_id": call_data.lead_id,
                "agent_id": call_data.user_id,
                "agent_name": call_data.user_name,
                "call_id": call_data.call_id,
                "duration": call_data.duration,
                "direction": call_data.direction,
                "disposition": call_data.disposition
            }
        )
        
        # Record metrics
        if hasattr(result, 'commitments'):
            COMMITMENT_COUNT.inc(len(result.commitments))
            for commitment in result.commitments:
                TASK_CREATION.labels(system=commitment.system).inc()
        
        logger.info(f"Successfully processed call {call_data.call_id}")
        return {
            "success": True,
            "message": "Call processed successfully",
            "call_id": call_data.call_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing call {call_data.call_id}: {str(e)}", exc_info=True)
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "call_id": call_data.call_id,
                "timestamp": datetime.now().isoformat()
            }
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {
        "success": False,
        "error": "Internal server error",
        "detail": str(exc),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000) 