from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import time

app = FastAPI()

# Initialize the Limiter with a global rate limit (e.g., 5 requests per minute)
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

# Register the rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()  # Record the start time
    response = await call_next(request)
    process_time = time.perf_counter() - start_time  # Calculate the process time
    response.headers["X-Process-Time"] = str(process_time)  # Set the process time header
    return response


@app.get("/")
@limiter.limit("2/minute")
async def root(request: Request):  # Add the `request` parameter here
    return {"message": "Welcome to the FastAPI & SlowAPI MVP!"}


@app.get("/items/{item_id}")
@limiter.limit("5/minute")
async def read_item(item_id: int, request: Request):
    return {"item_id": item_id}


@app.get("/status")
async def status():
    return {"status": "ok"}

# Custom error handling example for rate limiting
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests, please slow down!"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
