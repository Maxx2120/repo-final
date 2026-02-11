import aiohttp
import json
from ..config import settings
from ..models import Chat, User
from sqlalchemy.orm import Session

async def chat_with_ollama(db: Session, user: User, message: str, model: str = "tinyllama"):
    url = f"{settings.OLLAMA_BASE_URL}/chat"

    # Store user message
    user_chat = Chat(user_id=user.id, role="user", content=message, model=model)
    db.add(user_chat)
    db.commit()

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "stream": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_response = result.get("message", {}).get("content", "")

                    # Store AI response
                    ai_chat = Chat(user_id=user.id, role="assistant", content=ai_response, model=model)
                    db.add(ai_chat)
                    db.commit()

                    return {"response": ai_response}
                else:
                    return {"error": f"Ollama returned status {response.status}"}
    except Exception as e:
        return {"error": str(e)}

def get_chat_history(db: Session, user: User, limit: int = 50):
    return db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.timestamp.desc()).limit(limit).all()
