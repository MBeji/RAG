import chromadb
from chromadb.utils import embedding_functions
import os

VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "vector_db")
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2" # Make it a constant

def get_collection(collection_name_prefix: str = "rag_documents", embedding_model_name: str = DEFAULT_EMBEDDING_MODEL):
    """
    Gets or creates a ChromaDB collection, using a specific sentence-transformer model
    for its embedding function. The actual collection name will append a sanitized
    version of the embedding model name to the prefix.
    """
    # Sanitize model name for collection naming (e.g., replace slashes, dots)
    sanitized_model_name = embedding_model_name.replace("/", "_").replace(".", "_")
    effective_collection_name = f"{collection_name_prefix}_{sanitized_model_name}"

    # Initialize the embedding function with the specified model
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model_name)
    
    collection = client.get_or_create_collection(
        name=effective_collection_name,
        embedding_function=ef
    )
    return collection

def add_documents_to_store(
    text_chunks: list[str], 
    metadatas: list[dict] = None, 
    ids: list[str] = None,
    collection_name_prefix: str = "rag_documents", # Use prefix now
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL
):
    """
    Adds text chunks to the specified ChromaDB collection, using a specific embedding model.
    """
    collection = get_collection(collection_name_prefix, embedding_model_name)
    
    if not ids:
        # Generate IDs that include a hint of the model to help ensure uniqueness across collections if chunks are similar
        ids = [f"chunk_{i}_{collection.name}" for i in range(len(text_chunks))] 
    
    if not metadatas:
        metadatas = [{} for _ in range(len(text_chunks))]
    
    # Add embedding_model_name to metadata for clarity
    for i in range(len(metadatas)):
        metadatas[i]['embedding_model'] = embedding_model_name # Storing the original model name

    if not (len(text_chunks) == len(metadatas) == len(ids)):
        raise ValueError("text_chunks, metadatas, and ids must have the same number of elements.")

    collection.add(
        documents=text_chunks,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Added {len(text_chunks)} documents to collection '{collection.name}' using model '{embedding_model_name}'.")


def query_vector_store(
    query_text: str, 
    top_k: int = 5, 
    collection_name_prefix: str = "rag_documents",
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    relevance_score_threshold: float = None # If L2 distance, lower is better. e.g. 1.0 or 1.5 might be a starting point.
) -> dict:
    """
    Queries the vector store for the most similar documents to the query_text,
    optionally filtering by a relevance score threshold.

    Args:
        query_text: The text to search for.
        top_k: The number of results to initially retrieve.
        collection_name_prefix: Prefix for the collection name.
        embedding_model_name: The embedding model used for the collection.
        relevance_score_threshold: Maximum L2 distance for a result to be considered relevant.
                                   Lower values mean higher relevance (more similar).
                                   If None, no filtering is applied.

    Returns:
        A dictionary containing the query results (ids, documents, metadatas, distances).
    """
    collection = get_collection(collection_name_prefix, embedding_model_name)
    
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        include=['metadatas', 'documents', 'distances'] # Ensure distances are included
    )

    if relevance_score_threshold is not None and results.get('distances'):
        filtered_ids = []
        filtered_documents = []
        filtered_metadatas = []
        filtered_distances = []

        # Results are lists of lists (one inner list per query_text, we have one query_text)
        original_ids = results.get('ids', [[]])[0]
        original_documents = results.get('documents', [[]])[0]
        original_metadatas = results.get('metadatas', [[]])[0]
        original_distances = results.get('distances', [[]])[0]

        for i in range(len(original_documents)):
            # Assuming lower distance is better (e.g., L2 distance)
            if original_distances[i] < relevance_score_threshold:
                if original_ids: # Chroma might not return ids if collection is empty or ids were not provided initially
                     filtered_ids.append(original_ids[i])
                filtered_documents.append(original_documents[i])
                filtered_metadatas.append(original_metadatas[i])
                filtered_distances.append(original_distances[i])
        
        # Update results with filtered lists
        # Note: If original_ids was None/empty, filtered_ids will remain empty.
        # This is okay as ChromaDB might not always return IDs if they weren't explicitly set.
        results['ids'] = [filtered_ids] if original_ids else [[]] # Ensure correct structure
        results['documents'] = [filtered_documents]
        results['metadatas'] = [filtered_metadatas]
        results['distances'] = [filtered_distances]
        
        print(f"Query: '{query_text}'. Initial results: {len(original_documents)}. Filtered results (threshold < {relevance_score_threshold}): {len(filtered_documents)}.")

    return results

# Example Usage (in if __name__ == '__main__')
if __name__ == '__main__':
    # ... (previous example code from previous subtasks, if any, should be preserved or adapted) ...
    # For this specific test, we'll focus on the query_vector_store changes.
    
    print(f"ChromaDB persistent client initialized at: {VECTOR_DB_PATH}")

    # Example: Re-populate or ensure data exists for default model to test thresholding
    default_collection_for_test = get_collection(embedding_model_name=DEFAULT_EMBEDDING_MODEL)
    if default_collection_for_test.count() == 0:
        print(f"Populating collection '{default_collection_for_test.name}' for threshold test...")
        sample_chunks_for_test = [
            "The quick brown fox jumps over the lazy dog.", 
            "General information about vector databases and their importance in AI.", 
            "Exploring advanced AI concepts like neural networks and deep learning.",
            "Another document about vector databases, focusing on ChromaDB.",
            "A document discussing the theoretical aspects of vector embeddings."
        ]
        meta_for_test = [{"source": "test_doc.txt", "chunk_num": i} for i, _ in enumerate(sample_chunks_for_test)]
        # Let IDs be auto-generated by add_documents_to_store
        add_documents_to_store(sample_chunks_for_test, meta_for_test, embedding_model_name=DEFAULT_EMBEDDING_MODEL)
        print(f"Collection '{default_collection_for_test.name}' now has {default_collection_for_test.count()} documents.")
    else:
        print(f"Collection '{default_collection_for_test.name}' already has {default_collection_for_test.count()} documents.")

    print(f"\n--- Testing with Relevance Score Threshold using model '{DEFAULT_EMBEDDING_MODEL}' ---")
    query = "information about vector databases"
    print(f"Querying for: '{query}'")

    # Test without filter
    results_no_filter = query_vector_store(query, top_k=5, embedding_model_name=DEFAULT_EMBEDDING_MODEL)
    print(f"\nResults (no filter, top_k=5):")
    if results_no_filter.get('documents') and results_no_filter['documents'][0]:
        for i, doc_text in enumerate(results_no_filter['documents'][0]):
            dist = results_no_filter['distances'][0][i] if results_no_filter.get('distances') and results_no_filter['distances'][0] else 'N/A'
            print(f"  Doc: {doc_text[:50]}..., Dist: {dist}") # Print snippet
    else:
        print("  No results or empty documents list.")

    # Test with different thresholds
    # These values are illustrative; optimal thresholds depend on the model and data.
    # For L2 distance (default in ChromaDB for SentenceTransformers), smaller is better.
    # A common range for "good" L2 distances with normalized embeddings is < 1.0.
    thresholds_to_test = [1.5, 1.0, 0.7, 0.5, 0.3] 
    for thold in thresholds_to_test:
        print(f"\nResults (threshold < {thold}, top_k=5):")
        results_filtered = query_vector_store(query, top_k=5, embedding_model_name=DEFAULT_EMBEDDING_MODEL, relevance_score_threshold=thold)
        if results_filtered.get('documents') and results_filtered['documents'][0]:
            for i, doc_text in enumerate(results_filtered['documents'][0]):
                dist = results_filtered['distances'][0][i] if results_filtered.get('distances') and results_filtered['distances'][0] else 'N/A'
                print(f"  Doc: {doc_text[:50]}..., Dist: {dist}") # Print snippet
        else:
            print(f"  No results passed the threshold {thold}.")
            
    # Example of querying a potentially different model's collection (if populated from previous steps)
    other_model_example = "paraphrase-MiniLM-L3-v2" # As used in previous example
    other_collection_for_test = get_collection(embedding_model_name=other_model_example)
    if other_collection_for_test.count() > 0:
        print(f"\n--- Testing with Relevance Score Threshold using model '{other_model_example}' ---")
        query_other = "document content example" # Adjust query as needed for this model's content
        results_other_filtered = query_vector_store(query_other, top_k=3, embedding_model_name=other_model_example, relevance_score_threshold=1.0)
        print(f"Results for '{other_model_example}' (threshold < 1.0):")
        if results_other_filtered.get('documents') and results_other_filtered['documents'][0]:
            for i, doc_text in enumerate(results_other_filtered['documents'][0]):
                dist = results_other_filtered['distances'][0][i] if results_other_filtered.get('distances') and results_other_filtered['distances'][0] else 'N/A'
                print(f"  Doc: {doc_text[:50]}..., Dist: {dist}")
        else:
            print("  No results or empty documents list for other model with this threshold.")
    else:
        print(f"\nCollection for model '{other_model_example}' is empty or not found, skipping threshold test for it.")

    print(f"\nList of all collections: {[col.name for col in client.list_collections()]}")
