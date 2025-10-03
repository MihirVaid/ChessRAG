from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from retriever_tools import load_all_retriever_tools

def init_rag_agent():
    #Load retrievers fresh each time
    tools = load_all_retriever_tools()

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert in chess who can read and understand PGNs. "
                       "You have access to retriever tools with opening book and player games data. "
                       "Please provide responses as a chess expert."),
            ("user", "Question: {question}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]
    )

    #agent with fresh tools
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor
