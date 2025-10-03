import os
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from langchain_huggingface import HuggingFaceEmbeddings

VECTOR_FOLDER = "vector_stores"
OPENING_BOOK_PATH = "opening_book"

def load_all_retriever_tools():
    tools = []
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    if os.path.exists(VECTOR_FOLDER):
        for dirname in os.listdir(VECTOR_FOLDER):
            path = os.path.join(VECTOR_FOLDER, dirname)
            if os.path.isdir(path):
                try:
                    vectordb = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
                    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

                    # Tool name: ensure uniqueness
                    tool_name = f"{dirname}_retriever"

                    description = f"Retriever for vector store: {dirname}"

                    retriever_tool = create_retriever_tool(
                        retriever,
                        name=tool_name,
                        description=description
                    )
                    tools.append(retriever_tool)

                except Exception as e:
                    print(f"Could not load vector store {dirname}: {e}")

    #Load opening book retriever only once
    if os.path.exists(OPENING_BOOK_PATH):
        try:
            vectordb1 = FAISS.load_local(OPENING_BOOK_PATH, embeddings, allow_dangerous_deserialization=True)
            retriever = vectordb.as_retriever(search_kwargs={"k": 3})
            opening_retriever_tool = create_retriever_tool(
                opening_retriever,
                "opening_book_retriever",
                "Search for openings and their PGNs."
            )
            tools.append(opening_retriever_tool)
        except Exception as e:
            print(f"Could not load opening book: {e}")

    return tools

tools = load_all_retriever_tools()
print([t.name for t in tools])

