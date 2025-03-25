# +++ MODIFICATO PER DEEPSEEK +++
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import uuid  # <-- Aggiunto per gestione conversazioni

# Carica il prompt da file
with open("prompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read().strip()

app = FastAPI()

# Configurazione DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"

# Memorizza le conversazioni in memoria
conversations = {}

class ChatRequest(BaseModel):
    thread_id: str
    message: str

def call_deepseek(messages: list):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(DEEPSEEK_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DeepSeek API Error: {str(e)}")

@app.get('/start')
async def start_conversation():
    thread_id = str(uuid.uuid4())  # <-- Genera un ID univoco
    conversations[thread_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return {"thread_id": thread_id}

@app.post('/chat')
async def chat(chat_request: ChatRequest):
    thread_id = chat_request.thread_id
    user_message = chat_request.message

    if not thread_id or thread_id not in conversations:
        raise HTTPException(status_code=400, detail="Thread ID non valido")

    # Aggiungi messaggio utente alla cronologia
    conversations[thread_id].append({"role": "user", "content": user_message})
    
    try:
        # Ottieni risposta da DeepSeek
        assistant_response = call_deepseek(conversations[thread_id])
        
        # Aggiungi risposta alla cronologia
        conversations[thread_id].append({"role": "assistant", "content": assistant_response})
        
        return {"response": assistant_response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
