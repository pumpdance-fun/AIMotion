import chromadb
from datetime import datetime
from typing import List, Dict, Any, Optional
from data_struct import Dance, TokenImage
from dotenv import load_dotenv
import os

load_dotenv()

class ChromaDatabase:
    def __init__(self, persist_directory: Optional[str] = None):
        # Initialize with optional persistence or server connection
        if persist_directory:
            self.client = chromadb.Client(chromadb.Settings(
                persist_directory=persist_directory,
                chroma_db_impl="duckdb+parquet"
            ))
        else:
            # Connect to ChromaDB server
            self.client = chromadb.HttpClient(host='localhost', port=8000)
        
    def create_collection(self, name: str, description: str = "") -> chromadb.Collection:
        """Create a new collection or get existing one"""
        try:
            return self.client.create_collection(
                name=name,
                metadata={
                    "description": description,
                    "created": str(datetime.now())
                }
            )
        except ValueError:
            # If collection exists, get it
            return self.client.get_collection(name)
    
    def insert_documents(self, 
                        collection_name: str,
                        documents: List[str],
                        metadatas: List[Dict[str, Any]],
                        ids: List[str]) -> None:
        """Insert documents into a collection"""
        collection = self.client.get_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def insert_dances(self, dances: List[Dance], collection_name: str = "dance_videos") -> None:
        """Insert dance videos into the collection"""
        self.insert_documents(
            collection_name=collection_name,
            documents=[dance.document for dance in dances],
            metadatas=[dance.metadata for dance in dances],
            ids=[dance.id for dance in dances]
        )
    
    def insert_images(self, images: List[TokenImage], collection_name: str = "token_images") -> None:
        """Insert dance images into the collection"""
        self.insert_documents(
            collection_name=collection_name,
            documents=[image.document for image in images],
            metadatas=[image.metadata for image in images],
            ids=[image.id for image in images]
        )

    def query_documents(self,
                       collection_name: str,
                       query_texts: List[str],
                       n_results: int = 5,
                       **kwargs) -> Dict:
        """Query documents from a collection"""
        collection = self.client.get_collection(collection_name)
        return collection.query(
            query_texts=query_texts,
            n_results=n_results,
            **kwargs
        )

    def query_dances(self,
                     collection_name: str,
                     query_texts: List[str],
                     n_results: int = 5,
                     **kwargs) -> List[Dance]:
        """Query dances from a collection"""
        raw_results = self.query_documents(
            collection_name=collection_name,
            query_texts=query_texts,
            n_results=n_results,
            **kwargs
        )
        
        dances = []
        for i, metadata in enumerate(raw_results["metadatas"][0]):
            # Combine metadata with id and document
            dance_data = metadata.copy()
            dance_data['id'] = raw_results["ids"][0][i]
            dance_data['description'] = raw_results["documents"][0][i]
            dances.append(Dance.from_dict(dance_data))
            
        return dances
    
    def query_images(self,
                     collection_name: str,
                     query_texts: List[str],
                     n_results: int = 5,
                     **kwargs) -> List[TokenImage]:
        """Query images from a collection"""
        raw_results = self.query_documents(
            collection_name=collection_name,
            query_texts=query_texts,
            n_results=n_results,
            **kwargs
        )
        images = []
        for i, metadata in enumerate(raw_results["metadatas"][0]):
            # Combine metadata with id and document
            image_data = metadata.copy()
            image_data['id'] = raw_results["ids"][0][i]
            image_data['description'] = raw_results["documents"][0][i]
            images.append(TokenImage.from_dict(image_data))
        return images
    
    def delete_collection(self, name: str) -> None:
        """Delete a collection"""
        self.client.delete_collection(name)
        
    def list_collections(self) -> List[str]:
        """List all collections"""
        return self.client.list_collections()


if __name__ == "__main__":
    db = ChromaDatabase()

    # Query dances
    dances = db.query_dances(
        collection_name="dance_videos",
        query_texts=["hiphop"],
    )
    print(dances)

    # Query images
    images = db.query_images(
        collection_name="token_images",
        query_texts=["pepe"],
    )
    print(images)