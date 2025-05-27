"""
Vector Store - Enhanced integration with ChromaDB for document storage,
retrieval, and semantic search capabilities.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from langchain.docstore.document import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    Enhanced vector store manager for document storage and retrieval
    using ChromaDB and Ollama embeddings.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "mistral"):
        """
        Initialize the vector store manager.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            model_name: Name of the Ollama model to use for embeddings
        """
        self.persist_directory = persist_directory
        self.model_name = model_name
        
        # Create the persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model=model_name,
            temperature=0.0  # No randomness in embeddings
        )
        
        # Initialize ChromaDB
        self.db = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        
        # Initialize text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"VectorStoreManager initialized with model: {model_name}")

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, collection_name: str = "default") -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dictionaries
            collection_name: Name of the collection to add documents to
            
        Returns:
            List of document IDs
        """
        try:
            # Ensure metadatas has same length as texts
            if metadatas is None:
                metadatas = [{} for _ in texts]
            elif len(metadatas) != len(texts):
                logger.warning(f"Metadatas length ({len(metadatas)}) doesn't match texts length ({len(texts)}). Using empty metadata.")
                metadatas = [{} for _ in texts]
            
            # Add collection name to metadata
            for metadata in metadatas:
                metadata["collection"] = collection_name
            
            # Create document objects
            documents = [
                LangchainDocument(page_content=text, metadata=metadata)
                for text, metadata in zip(texts, metadatas)
            ]
            
            # Add documents to the vector store
            ids = self.db.add_documents(documents)
            
            # Persist the changes
            self.db.persist()
            
            logger.info(f"Added {len(ids)} documents to collection '{collection_name}'")
            return ids
        
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return []

    def add_chunked_document(self, text: str, metadata: Optional[Dict[str, Any]] = None, collection_name: str = "default") -> List[str]:
        """
        Add a document to the vector store with automatic chunking.
        
        Args:
            text: Document text
            metadata: Optional metadata dictionary
            collection_name: Name of the collection to add the document to
            
        Returns:
            List of chunk IDs
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Prepare metadata for each chunk
            if metadata is None:
                metadata = {}
            
            metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["collection"] = collection_name
                chunk_metadata["chunk_id"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                metadatas.append(chunk_metadata)
            
            # Add chunks to the vector store
            return self.add_documents(chunks, metadatas, collection_name)
        
        except Exception as e:
            logger.error(f"Error adding chunked document: {str(e)}")
            return []

    def search(self, query: str, collection_name: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query
            collection_name: Optional collection name to filter results
            k: Number of results to return
            
        Returns:
            List of dictionaries with document content and metadata
        """
        try:
            # Prepare filter if collection name is provided
            filter_dict = {"collection": collection_name} if collection_name else None
            
            # Perform similarity search
            results = self.db.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": score
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

    def search_by_metadata(self, metadata_filter: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents by metadata values.
        
        Args:
            metadata_filter: Dictionary of metadata field-value pairs to match
            k: Number of results to return
            
        Returns:
            List of dictionaries with document content and metadata
        """
        try:
            # Convert metadata filter to ChromaDB format
            filter_dict = {}
            for key, value in metadata_filter.items():
                filter_dict[key] = {"$eq": value}
            
            # Perform search
            results = self.db.get(
                where=filter_dict,
                limit=k
            )
            
            # Format results
            formatted_results = []
            if results and len(results["documents"]) > 0:
                for i in range(len(results["documents"])):
                    formatted_results.append({
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "id": results["ids"][i]
                    })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching by metadata: {str(e)}")
            return []

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary with document content and metadata, or None if not found
        """
        try:
            # Get document by ID
            results = self.db.get(ids=[doc_id])
            
            # Check if document was found
            if results and len(results["documents"]) > 0:
                return {
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0],
                    "id": results["ids"][0]
                }
            else:
                logger.warning(f"Document with ID '{doc_id}' not found")
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving document by ID: {str(e)}")
            return None

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete document
            self.db.delete(ids=[doc_id])
            
            # Persist changes
            self.db.persist()
            
            logger.info(f"Deleted document with ID: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete all documents in a collection.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all documents in the collection
            results = self.search_by_metadata({"collection": collection_name}, k=1000)
            
            # Extract document IDs
            doc_ids = [result["id"] for result in results]
            
            if doc_ids:
                # Delete documents
                self.db.delete(ids=doc_ids)
                
                # Persist changes
                self.db.persist()
                
                logger.info(f"Deleted collection '{collection_name}' with {len(doc_ids)} documents")
            else:
                logger.info(f"No documents found in collection '{collection_name}'")
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False

    def get_collections(self) -> List[str]:
        """
        Get a list of all collections in the vector store.
        
        Returns:
            List of collection names
        """
        try:
            # Get all documents
            results = self.db.get()
            
            # Extract unique collection names
            collections = set()
            if results and "metadatas" in results and results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "collection" in metadata:
                        collections.add(metadata["collection"])
            
            return list(collections)
        
        except Exception as e:
            logger.error(f"Error getting collections: {str(e)}")
            return []

    def count_documents(self, collection_name: Optional[str] = None) -> int:
        """
        Count documents in the vector store, optionally filtered by collection.
        
        Args:
            collection_name: Optional collection name to filter by
            
        Returns:
            Number of documents
        """
        try:
            # Prepare filter if collection name is provided
            filter_dict = {"collection": {"$eq": collection_name}} if collection_name else None
            
            # Get document count
            return self.db._collection.count(filter_dict)
        
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            return 0

    def __del__(self):
        """
        Ensure changes are persisted when the manager is destroyed.
        """
        try:
            self.db.persist()
            logger.info("Vector store persisted")
        except:
            pass
