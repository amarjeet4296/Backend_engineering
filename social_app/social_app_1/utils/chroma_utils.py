from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
import os

class ChromaManager:
    def __init__(self):
        """
        Initialize the Chroma vector store manager with Ollama embeddings.
        """
        self.embeddings = OllamaEmbeddings(
            model="mistral",
            temperature=0.0  # No randomness in embeddings
        )
        
        # Create persist directory if it doesn't exist
        persist_dir = "./chroma_policies"
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize Chroma database
        self.db = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )

    def search_documents(self, namespace: str, query: str, k: int = 3):
        """
        Search for relevant documents in the vector store.
        
        Args:
            namespace (str): The namespace to search in
            query (str): The search query
            k (int): Number of results to return
            
        Returns:
            List[str]: List of document contents
        """
        try:
            # Perform similarity search
            results = self.db.similarity_search(
                query,
                k=k,
                filter={"namespace": namespace} if namespace else None
            )
            
            # Extract and return document contents
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    def add_documents(self, texts: list, metadatas: list = None):
        """
        Add documents to the vector store.
        
        Args:
            texts (list): List of document texts
            metadatas (list): List of metadata dictionaries
        """
        try:
            self.db.add_texts(
                texts=texts,
                metadatas=metadatas or [{}] * len(texts)
            )
            self.db.persist()
        except Exception as e:
            print(f"Error adding documents: {str(e)}")

    def __del__(self):
        """
        Cleanup when the manager is destroyed.
        """
        try:
            self.db.persist()
        except:
            pass 