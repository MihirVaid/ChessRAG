import os
import re
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.docstore.document import Document
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
load_dotenv()
os.environ['GOOGLE_API_KEY'] = os.getenv("GOOGLE_API_KEY")

GAMES_FILE = "games.txt"
VECTOR_FOLDER = "vector_stores"
VECTOR_PATH = os.path.join(VECTOR_FOLDER, "my_games")

#ensure files exist
def ensure_file():
    if not os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, "w", encoding="utf-8") as f:
            f.write("=== Chess Games Log ===\n\n")

#save pgn and vectorizeand update
def save_manual_pgn(pgn_text: str):
    """Save a manually pasted PGN into games.txt and update FAISS incrementally"""
    ensure_file()
    with open(GAMES_FILE, "r", encoding="utf-8") as f:
        existing_text = f.read()
        game_count = existing_text.count("=== Game")

    new_game_number = game_count + 1
    today = datetime.now().strftime("%d-%m-%Y")

    entry = f"\n=== Game {new_game_number} ({today}) ===\n{pgn_text.strip()}\n"

    with open(GAMES_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

    #new game doc only
    header = f"=== Game {new_game_number} ({today}) ==="
    doc = Document(page_content=f"{header}\n{pgn_text.strip()}")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    os.makedirs(VECTOR_FOLDER, exist_ok=True)

    #if FAISS already exists, load & append
    if os.path.exists(VECTOR_PATH):
        vectordb = FAISS.load_local(VECTOR_PATH, embeddings, allow_dangerous_deserialization=True)
        vectordb.add_documents([doc])
    else:
        vectordb = FAISS.from_documents([doc], embeddings)

    vectordb.save_local(VECTOR_PATH)

    return new_game_number, f"✅ Game {new_game_number} embedded and saved at {VECTOR_PATH}"

def get_last_two_games():
    """Retrieve the last two saved games from games.txt"""
    ensure_file()
    with open(GAMES_FILE, "r", encoding="utf-8") as f:
        games_text = f.read().strip().split("=== Game")
        if len(games_text) > 1:
            last_two = games_text[-2:] if len(games_text) > 2 else games_text[1:]
            return [f"=== Game{g.strip()}" for g in last_two]
        else:
            return []
