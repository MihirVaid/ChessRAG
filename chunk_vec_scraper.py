import requests
import os
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
os.environ['GOOGLE_API_KEY']= os.getenv("GOOGLE_API_KEY")
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from langchain.docstore.document import Document
# helps bypass chesscomapi
HEADERS = {"User-Agent": "MyChessApp/1.0"}

def clean_pgn(pgn: str) -> str:
    """Clean PGN to keep only essential headers and strip clock annotations + fix moves."""

    keep_headers = {"Site", "Date", "White", "Black", "Result",
                    "ECO", "ECOUrl", "WhiteElo", "BlackElo",
                    "Termination", "Link"}

    cleaned_lines = []
    moves_started = False
    moves_buffer = []

    for line in pgn.splitlines():
        line = line.strip()

        if line.startswith("["):
            header_name = line.split(" ", 1)[0].strip("[]")
            if header_name in keep_headers:
                cleaned_lines.append(line)

        elif line and not line.startswith("["):
            #move text
            if not moves_started:
                moves_started = True
                cleaned_lines.append("")  #blank line

            #Remove annotations like {[%clk ...]}
            line = re.sub(r"\{.*?\}", "", line)

            #Fix duplicate move numbers: "1. d4 1... Nf6" → "1. d4 Nf6"
            line = re.sub(r"(\d+)\.\s*([^ ]+)\s*\d+\.\.\.\s*([^ ]+)", r"\1. \2 \3", line)

            moves_buffer.append(line.strip())

    # Join all moves into a single line
    if moves_buffer:
        cleaned_lines.append(" ".join(moves_buffer).strip())

    return "\n".join(cleaned_lines).strip()

def save_game(pgn, game_number, date, filename):
    """Append a cleaned PGN game to the text file."""
    cleaned_pgn = clean_pgn(pgn)
    entry = f"\n=== Game {game_number} ({date}) ===\n{cleaned_pgn}\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(entry)








# --- Chunking utility ---
def split_chess_games(text: str = None, file_path: str = None, keep_header: bool = True):
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    elif text is None:
        raise ValueError("Provide either 'text' or 'file_path'.")

    headers = re.findall(r"=== Game \d+.*?===", text)
    contents = re.split(r"=== Game \d+.*?===", text)
    contents = [c.strip() for c in contents if c.strip()]

    games = []
    for i, content in enumerate(contents):
        header = headers[i] if keep_header and i < len(headers) else ""
        game_text = f"{header}\n{content}" if header else content
        games.append(Document(page_content=game_text))

    return games

# --- Embedding + Vectorization ---
def vectorize_games(file_path: str, vector_folder: str = "vector_stores"):
    os.makedirs(vector_folder, exist_ok=True)

    # Split into documents
    splitted_games = split_chess_games(file_path=file_path)

    if not splitted_games:
        return None, " No games found to vectorize."

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = FAISS.from_documents(splitted_games, embeddings)

    # Persist vector DB
    index_name = os.path.splitext(os.path.basename(file_path))[0]
    save_path = os.path.join(vector_folder, index_name)
    vectordb.save_local(save_path)

    return vectordb, f" Vector store created & saved at {save_path}"

# --- Fetch + Process Games ---
def fetch_games(username, game_format="all", months=None, folder="saved_games"):
    """
    Fetch Chess.com games by username and format, then vectorize them.
    """
    os.makedirs(folder, exist_ok=True)

    filename = os.path.join(folder, f"{username}_{game_format}.txt")

    # Reset file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"=== {username} {game_format.capitalize()} Games Log ===\n\n")

    archive_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    resp = requests.get(archive_url, headers=HEADERS)
    if resp.status_code != 200:
        return f"❌ Error fetching archives: {resp.status_code}"

    archives = resp.json().get("archives", [])
    if months:
        archives = archives[-months:]

    game_count = 0

    for month_url in archives:
        r = requests.get(month_url, headers=HEADERS)
        if r.status_code != 200:
            continue

        data = r.json()
        for game in data.get("games", []):
            pgn = game.get("pgn", "")
            time_class = game.get("time_class", "").lower()

            if not pgn:
                continue
            if game_format != "all" and time_class != game_format:
                continue

            date = datetime.fromtimestamp(game["end_time"]).strftime("%d-%m-%Y")
            game_count += 1
            save_game(pgn, game_count, date, filename)

    #  After saving, immediately chunk + vectorize
    vectordb, vec_msg = vectorize_games(filename)

    return f" Saved {game_count} {game_format.capitalize()} games to {filename}\n{vec_msg}"
