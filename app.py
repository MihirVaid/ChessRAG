import streamlit as st
import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from chunk_vec_save import save_manual_pgn, get_last_two_games
from chunk_vec_scraper import fetch_games
from rag_agent import init_rag_agent
from pgn_viewer_board import run_pgn_viewer   

#eventloop
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
nest_asyncio.apply()
#env
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"

st.title("Chess Assistant")
st.sidebar.title("Tools")
page = st.sidebar.radio(
    "Go to:",
    ["Home", "PGN Saver", "PGN Scraper", "PGN Viewer", "RAG Agent"]
)
if st.sidebar.button("🔄 Reload RAG Tools"):
    with st.spinner("Loading new retrievers..."):
        st.session_state.agent_executor = init_rag_agent()
    st.success("RAG Agent reloaded with updated tools")

#HOME
if page == "Home":
    st.write("Welcome! Use the sidebar to select a tool.")
    st.markdown(
    """
    #### Modules Overview  

    ##### PGN Saver  
    - Lets you save custom PGNs from your games and store them in vectors.  
    - Updates your existing file and vectors when a new game is added.  

    ##### PGN Scraper  
    - Lets you fetch games from any Chess.com ID.  
    - Automatically chunks them and saves them in vectors.  

    ##### ChessBoard  
    - A PGN Viewer which lets you paste a PGN and replay moves interactively.  
    - Supports move navigation, restart, and board flipping.  

    ##### RAG Agent  
    - Uses the saved/scraped games to answer chess-related queries.  
    - Accesses the Opening Book to answer opening-related questions.  
    """
    )

          
#PGN Saver
elif page == "PGN Saver":
    st.header("Save Your PGN Games")

    pgn_input = st.text_area("Paste your PGN here:", height=300)

    if st.button("Save Game"):
        if pgn_input.strip():
            game_number, vec_msg = save_manual_pgn(pgn_input.strip())
            st.success(f"✅ Game {game_number} saved!")
            st.info(vec_msg)   # show vectorization message
        else:
            st.warning("⚠️ Please paste a PGN before saving.")

    if st.button("Show Last 2 Saved Games"):
        last_two = get_last_two_games()
        if last_two:
            st.subheader("Last 2 Saved Games")
            for g in last_two:
                st.text(g)
        else:
            st.info("No games saved yet.")

#PGN Scraper
elif page == "PGN Scraper":
    st.header("Fetch Games from Chess.com")

    username = st.text_input("Enter Chess.com username:")
    game_format = st.selectbox("Choose format:", ["all", "bullet", "blitz", "rapid"])
    months = st.slider("How many past months to fetch?", 1, 24, 3)

    if st.button("Fetch Games"):
        if username.strip():
            result = fetch_games(username.strip(), game_format, months)
            st.success(result)

            # Preview last 2 games
            filename = os.path.join("saved_games", f"{username.strip()}_{game_format}.txt")
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    games_text = f.read().strip().split("=== Game")
                    if len(games_text) > 1:
                        last_two = games_text[-2:] if len(games_text) > 2 else games_text[1:]
                        st.subheader("Last 2 Scraped Games")
                        for g in last_two:
                            st.text(f"=== Game{g.strip()}")
                    else:
                        st.info("No games found in the file.")
        else:
            st.warning("⚠️ Please enter a username.")

#PGN Viewer
elif page == "PGN Viewer":
    run_pgn_viewer()

#RAG Agent
elif page == "RAG Agent":
    st.header("Chess RAG Assistant")

    input_text = st.text_input(
        "Ask your chess question (e.g. opponent's winrate in Sicilian Defense)"
    )
    
    if "agent_executor" not in st.session_state:
        st.session_state.agent_executor = init_rag_agent()

    if input_text:
        result = st.session_state.agent_executor.invoke({"question": input_text})
        st.subheader("Answer:")
        st.write(result["output"])

