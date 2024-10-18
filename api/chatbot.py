from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

class SimpleChatbotManager:
    def __init__(self, resume_path):
        load_dotenv()
        
        # Get the API key
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

        # Initialize LLM and embeddings
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            max_tokens=4092,
            temperature=0.8,
            top_p=0.5,
            repetition_penalty=1
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Store resume path
        self.resume_path = resume_path
        
        # Vector store for resume
        self.vector_store = None

        # QA chain
        self.qa_chain = None

        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            k=5,
            return_messages=True
        )

        # Custom prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["chat_history", "context", "question"],
            template="""You are an AI assistant designed to answer questions about Viral Biyawala based on his resume. 
            Use the following pieces of context to answer the question at the end.

            Chat History: {chat_history}
            Context: {context}
            Question: {question}

            Answer:"""
        )

    def load_pdf(self):
        """Loads and processes the PDF resume."""
        try:
            print(f"Loading PDF from {self.resume_path}")
            loader = PyPDFLoader(self.resume_path)
            return loader.load()
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            return None

    def split_documents(self, documents):
        """Splits documents into smaller chunks."""
        try:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=400)
            return text_splitter.split_documents(documents)
        except Exception as e:
            print(f"Error splitting documents: {str(e)}")
            return None

    def create_vector_store(self, documents):
        """Creates a vector store for the resume."""
        try:
            print("Creating vector store for resume")
            docs_split = self.split_documents(documents)
            self.vector_store = FAISS.from_documents(docs_split, self.embeddings)
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")

    def initialize_source(self):
        """Loads, processes, and stores the resume."""
        resume_docs = self.load_pdf()
        if resume_docs:
            self.create_vector_store(resume_docs)
            self.setup_qa_chain()

    def setup_qa_chain(self):
        """Sets up the QA chain using the resume vector store."""
        if self.vector_store:
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
                memory=self.memory,
                combine_docs_chain_kwargs={"prompt": self.prompt_template}
            )
        else:
            print("Error: Vector store not initialized")

    def run_query(self, query):
        """Executes a query using the QA chain."""
        if not self.qa_chain:
            return "Error: QA chain not initialized. Please make sure the resume is loaded correctly."

        try:
            response = self.qa_chain({"question": query})
            answer = response['answer']
            
            if not answer or answer.strip() == "":
                return "Sorry, I couldn't find an answer to your query. Could you rephrase or ask something else?"
            
            return answer
        
        except Exception as e:
            print(f"\nError during query execution: {str(e)}\n\n")
            return "Oops! Something went wrong while processing your request. Please try again."

# Usage example
if __name__ == "__main__":
    chatbot_manager = SimpleChatbotManager(resume_path="resume_output.pdf")
    chatbot_manager.initialize_source()

    print("Chatbot initialized. You can now ask questions about Viral Biyawala based on his resume.")
    print("Type 'quit' to exit the program.")

    while True:
        query = input("\nYour question: ")
        if query.lower() == 'quit':
            break
        response = chatbot_manager.run_query(query)
        print(f"\nResponse: {response}")

    print("Thank you for using the chatbot. Goodbye!")