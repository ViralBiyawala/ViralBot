from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.agents import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate

class ChatbotManager:
    def __init__(self, resume_path, portfolio_urls, github_project_urls):
        load_dotenv()
        
        # Get the API key
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

        # Initialize LLM and embeddings
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            max_tokens=8192,     # Set max token size
            temperature=0.1,    # Set temperature
            top_p=0.9,          # Optional: Set top_p for nucleus sampling
            repetition_penalty=2  # Optional: Set repetition penalty
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Store paths and URLs
        self.resume_path = resume_path
        self.portfolio_urls = portfolio_urls
        self.github_project_urls = github_project_urls
        
        # Memory for conversation context
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Vector stores to store embeddings for each source
        self.vector_stores = {
            "resume": None,
            "portfolio": None,
            "github": None
        }

        # Prompt template for the agent
        self.prompt_template = PromptTemplate.from_template(
            """You are an AI assistant built by Viral Biyawala to help answer user questions. You have access to the following tools to assist with this task:

        {tools}

        Use the following format:

        Question: The input question you must answer
        Thought: Analyze what steps are needed to answer the question.
        Action: If necessary, choose the relevant source or tool (one of [{tool_names}]) to gather the required information.
           - Case: If an action has already been performed or the information has been retrieved, do not repeat the same tool twice.
        Action Input: The specific input to be used for the action.
        Observation: The result of the action from the tool or source.
        ... (this Thought/Action/Action Input/Observation can repeat N times, with no repeated actions)
        Thought: Now summarize or finalize the answer.
        Final Answer: Provide the final answer to the original input question.

        Begin!

        Previous conversation history:
        {chat_history}

        Current question: {input}

        {agent_scratchpad}"""
        )

    def load_pdf(self, pdf_path):
        """Loads and processes a PDF document."""
        try:
            print(f"Loading PDF from {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            return loader.load()
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            return None

    def load_webpages(self, urls):
        """Loads and processes multiple webpages."""
        all_docs = []
        for url in urls:
            try:
                print(f"Loading webpage from {url}")
                loader = WebBaseLoader(url)
                web_docs = loader.load()
                all_docs.extend(web_docs)
            except Exception as e:
                print(f"Error loading webpage {url}: {str(e)}")
        return all_docs

    def split_documents(self, documents):
        """Splits documents into smaller chunks."""
        try:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
            return text_splitter.split_documents(documents)
        except Exception as e:
            print(f"Error splitting documents: {str(e)}")
            return None

    def create_vector_store(self, documents, source_name):
        """Creates a vector store for a given set of documents."""
        try:
            print(f"Creating vector store for {source_name}")
            docs_split = self.split_documents(documents)
            vector_store = FAISS.from_documents(docs_split, self.embeddings)
            self.vector_stores[source_name] = vector_store
        except Exception as e:
            print(f"Error creating vector store for {source_name}: {str(e)}")

    def initialize_sources(self):
        """Loads, processes, and stores the resume, portfolio, and GitHub projects."""
        
        # Load and create vector store for resume
        resume_docs = self.load_pdf(self.resume_path)
        if resume_docs:
            self.create_vector_store(resume_docs, "resume")

        # Load and create vector store for portfolio
        portfolio_docs = self.load_webpages(self.portfolio_urls)
        if portfolio_docs:
            self.create_vector_store(portfolio_docs, "portfolio")

        # Load and create vector store for GitHub projects
        github_docs = self.load_webpages(self.github_project_urls)
        if github_docs:
            self.create_vector_store(github_docs, "github")

    def create_retriever(self, source_name):
        """Creates a retriever for a given source vector store."""
        try:
            return self.vector_stores[source_name].as_retriever()
        except KeyError:
            print(f"Error: No vector store found for {source_name}")
            return None

    def setup_qa_chain(self, retriever, source_name):
        """Creates a QA chain using a retriever."""
        try:
            return create_retriever_tool(retriever, source_name, f"Search information from {source_name}.")
        except Exception as e:
            print(f"Error setting up QA chain: {str(e)}")
            return None

    def create_agent(self):
        """Sets up the agent with the resume, portfolio, and GitHub sources."""
        tools = []
        
        # Create retrievers for each source and add them as tools
        for source_name in ["resume", "portfolio", "github"]:
            retriever = self.create_retriever(source_name)
            if retriever:
                qa_chain = self.setup_qa_chain(retriever, source_name)
                tools.append(qa_chain)

        # Initialize the agent with the tools and memory
        self.agent = create_react_agent(
            llm=self.llm,
            prompt=self.prompt_template,
            tools=tools
        )

        # Initialize the agent executor
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=tools,
            memory=self.memory,
            verbose=False,
            handle_parsing_errors=True
        )

        return self.agent_executor

    def run_query(self, agent_executor, query):
        """Executes a query through the agent."""
        try:
            # Replace vague terms with "Viral Biyawala"
            query = query.replace("him", "Viral Biyawala").replace("the person", "Viral Biyawala").replace("about him", "about Viral Biyawala")
            
            response = agent_executor.invoke({"input": query})
            
            # Handle case where no response is returned or answer is insufficient
            if not response['output'] or response['output'].strip() == "":
                return "Sorry, I couldn't find an answer to your query. Could you rephrase or ask something else?"
            
            return response['output']
        
        except Exception as e:
            print(f"\nError during query execution: {str(e)}\n\n")
            return "Oops! Something went wrong while processing your request. Please try again."


demo_github_projects = [
    "https://github.com/ViralBiyawala/Stanford_LLM_Tutor",
    "https://github.com/ShivamSikotra11/MHA",
    "https://github.com/jitanshuraut/Learn-AI-Studio",
    "https://github.com/ViralBiyawala/ATLAS-PowerBI",
    "https://github.com/ViralBiyawala/BBMS",
    "https://github.com/ViralBiyawala/ViralShare",
    "https://github.com/ViralBiyawala/Portfolio",
    "https://github.com/ViralBiyawala/DS_ML_Projects/tree/main/A_Visual_History_of_Nobel_Prize_Winners",
    "https://github.com/ViralBiyawala/DS_ML_Projects/tree/main/Dr._Semmelweis_and_the_Discovery_of_Handwashing",
    "https://www.datacamp.com/datalab/w/058082b0-6db9-4b7e-a510-faa8de89f91d"
]

# Define the portfolio URLs and demo GitHub projects
portfolio_urls = [
    "https://github.com/ViralBiyawala/ViralBiyawala",
    "https://viralbiyawala.pythonanywhere.com/index",
    "https://viralbiyawala.pythonanywhere.com/education",
    "https://viralbiyawala.pythonanywhere.com/certification",
    "https://viralbiyawala.pythonanywhere.com/project"
]

# Initialize the ChatbotManager with required inputs
chatbot_manager = ChatbotManager(
    resume_path="ViralBiyawala_resume.pdf",
    portfolio_urls=portfolio_urls,
    github_project_urls=demo_github_projects
)
# Step 1: Initialize the document sources
chatbot_manager.initialize_sources()

# Step 2: Create the agent
agent_executor = chatbot_manager.create_agent()


# response = chatbot_manager.run_query(agent_executor, 'user_query')

# create a fastapi api interface to interact with the chatbot deplyed through the vercel server
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Query(BaseModel):
    query: str

@app.post("/chatbot/")
def chatbot(query: Query):
    response = chatbot_manager.run_query(agent_executor, query.query)
    return {"response": response}

# Run the FastAPI server
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)