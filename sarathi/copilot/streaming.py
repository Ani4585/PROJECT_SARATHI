"""
Real-Time Asynchronous Multi-Modal Response Streamer.
"""
import asyncio
from typing import AsyncGenerator, List, Dict, Any

class StreamingResponseGenerator:
    @staticmethod
    async def stream_tokens(text: str, chunk_size: int = 4, delay_sec: float = 0.001) -> AsyncGenerator[str, None]:
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            yield chunk
            if delay_sec > 0:
                await asyncio.sleep(delay_sec)
