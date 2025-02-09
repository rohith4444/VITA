from fastapi import Request
import time
from src.utils.logger import setup_logger
import json

logger = setup_logger("APILogger")

async def log_request_middleware(request: Request, call_next):
    """Middleware to log request and response details"""
    # Generate request ID
    request_id = str(time.time())
    
    # Log request
    logger.info(f"Request [{request_id}] Started")
    try:
        # Log request details
        body = await request.body()
        if body:
            try:
                body_json = json.loads(body)
                logger.info(f"Request [{request_id}] Body: {json.dumps(body_json, indent=2)}")
            except:
                logger.info(f"Request [{request_id}] Body: {body.decode()}")
                
        logger.info(f"Request [{request_id}] URL: {request.url}")
        logger.info(f"Request [{request_id}] Method: {request.method}")
        logger.info(f"Request [{request_id}] Headers: {dict(request.headers)}")
        
        # Get response
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(f"Request [{request_id}] Completed in {process_time:.3f}s")
        logger.info(f"Request [{request_id}] Status: {response.status_code}")
        
        return response
        
    except Exception as e:
        logger.error(f"Request [{request_id}] Failed: {str(e)}")
        raise