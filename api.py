from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pipeline import run_research_pipeline_stream
import uvicorn

app = FastAPI()

@app.get("/api/research")
async def research_endpoint(topic: str):
    def event_stream():
        for event in run_research_pipeline_stream(topic):
            # Format required for Server-Sent Events (SSE)
            yield f"data: {event}\n\n" 
            
    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    