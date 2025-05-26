import chromadb
from chromadb.utils import embedding_functions
import os

# Define the path for persistent storage of ChromaDB
# This path is relative to this file (chroma_db.py)
# So, ../../vector_db means it will create vector_db folder at the root of rag-chatbot/
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "vector_db")
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

# Using SentenceTransformer for embeddings
# You can use a specific model from Hugging Face or a default one provided by chromadb
# For chromadb's default SentenceTransformer (uses all-MiniLM-L6-v2):
# If you want to be explicit with sentence-transformers library:
# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer('all-MiniLM-L6-v2')
# def embed_texts(texts):
#     return model.encode(texts).tolist()
# chroma_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Initialize ChromaDB Persistent Client
client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

# Default embedding function (Sentence Transformers)
# Uses all-MiniLM-L6-v2 by default.
# Ensure sentence-transformers is installed.
default_ef = embedding_functions.SentenceTransformerEmbeddingFunction()

def get_collection(collection_name: str = "rag_documents", embedding_function = default_ef):
    """Gets or creates a ChromaDB collection."""
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function # Using chromadb's wrapper for SentenceTransformer
    )
    return collection

def add_documents_to_store(
    text_chunks: list[str], 
    metadatas: list[dict] = None, 
    ids: list[str] = None,
    collection_name: str = "rag_documents"):
    """
    Adds text chunks, their embeddings, and metadatas to the specified ChromaDB collection.

    Args:
        text_chunks: A list of text strings.
        metadatas: A list of metadata dictionaries for each text chunk.
        ids: A list of unique IDs for each text chunk.
        collection_name: The name of the collection to add documents to.
    """
    collection = get_collection(collection_name)

    # ChromaDB's add method handles embedding generation internally if an embedding_function is set for the collection
    # If metadatas or ids are not provided for all chunks, you might need to generate them
    # or ensure the lists match the length of text_chunks.
    
    if not ids:
        # Basic ID generation if not provided, though it's better to have more meaningful IDs
        ids = [f"chunk_{i}" for i in range(len(text_chunks))]
    
    if not metadatas:
        metadatas = [{} for _ in range(len(text_chunks))]
    
    if not (len(text_chunks) == len(metadatas) == len(ids)):
        raise ValueError("text_chunks, metadatas, and ids must have the same number of elements.")

    collection.add(
        documents=text_chunks,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Added {len(text_chunks)} documents to collection '{collection_name}'.")


# Example Usage (optional, for testing within this file)
if __name__ == '__main__':
    # Ensure the vector_db directory will be created at rag-chatbot/vector_db
    print(f"ChromaDB persistent client initialized at: {VECTOR_DB_PATH}")

    # Test adding documents
    sample_chunks = [
        "This is the first document chunk.",
        "This is the second document chunk about AI.",
        "The third chunk discusses vector databases."
    ]
    sample_metadatas = [
        {"source": "doc1.txt", "chunk_num": 1},
        {"source": "doc1.txt", "chunk_num": 2},
        {"source": "doc2.pdf", "chunk_num": 1}
    ]
    sample_ids = ["doc1_chunk1", "doc1_chunk2", "doc2_chunk1"]

    try:
        add_documents_to_store(sample_chunks, sample_metadatas, sample_ids)
        
        # Verify collection count
        collection = get_collection()
        print(f"Collection '{collection.name}' now has {collection.count()} documents.")

        # Test with minimal inputs (auto-generated IDs and empty metadata)
        # add_documents_to_store(["Another chunk"], [{"source": "test.txt"}], ["test_chunk1"])
        # print(f"Collection '{collection.name}' now has {collection.count()} documents.")

    except Exception as e:
        print(f"Error during example usage: {e}")


def query_vector_store(query_text: str, top_k: int = 5, collection_name: str = "rag_documents") -> dict:
    """
    Queries the vector store for the most similar documents to the query_text.

    Args:
        query_text: The text to search for.
        top_k: The number of results to return.
        collection_name: The name of the collection to query.

    Returns:
        A dictionary containing the query results (ids, documents, metadatas, distances).
    """
    collection = get_collection(collection_name)
    
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        # include=['metadatas', 'documents', 'distances'] # This is often default
    )
    return results

# Example usage for query_vector_store (optional, for testing within chroma_db.py)
if __name__ == '__main__':
    # ... (existing example usage for adding documents) ...
    
    print("\nTesting query function...")
    # Ensure some documents were added first from the add_documents_to_store example
    if get_collection().count() > 0:
        query_results = query_vector_store("What is AI?", top_k=2)
        print(f"Query results for 'What is AI?':")
        if query_results and query_results.get('documents') and query_results['documents'][0]: # Check if documents list is not empty
            for i, doc in enumerate(query_results['documents'][0]):
                print(f"  Document: {doc}")
                if query_results['metadatas'] and query_results['metadatas'][0]:
                    print(f"  Metadata: {query_results['metadatas'][0][i]}")
                if query_results['distances'] and query_results['distances'][0]:
                    print(f"  Distance: {query_results['distances'][0][i]}")
        else:
            print("No results found or error in query structure.")
            print(f"Raw results: {query_results}") # Print raw results for debugging
    else:
        print("Skipping query test as no documents are in the collection.")
