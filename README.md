# ChessRAG
RAG Agent for chess Q&amp;A with LangChain + Gemini


#### Modules Overview  

#### PGN Saver  
- Lets you save custom PGNs from your games and store them in vectors.  
- Updates your existing file and vectors when a new game is added.  

#### PGN Scraper  
- Lets you fetch games from any Chess.com ID.  
- Automatically chunks them and saves them in vectors.  

 #### ChessBoard  
  - A PGN Viewer which lets you paste a PGN and replay moves interactively.  
  - Supports move navigation, restart, and board flipping.  

 #### RAG Agent  
  - Uses the saved/scraped games to answer chess-related queries.  
  - Accesses the Opening Book to answer opening-related questions.  
