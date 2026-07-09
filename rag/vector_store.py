class ChromaVectorStore:
    def __init__(self, db_path: str = "chroma_db", collection_name: str = "documents"):
        import chromadb
        client = chromadb.PersistentClient(path=db_path)
        self.collection = client.get_or_create_collection(collection_name)

    def search(self, query_vector: list[float], user_id: int, document_id: int | None = None, top_k: int = 5) -> list[dict]:
        if document_id is not None:
            where = {"$and": [{"user_id": user_id}, {"document_id": document_id}]}
        else:
            where = {"user_id": user_id}

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where,
        )

        output = []
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for text, metadata, distance in zip(documents, metadatas, distances):
            similarity = 1 - distance
            output.append({
                "section": metadata["section"],
                "text": text,
                "similarity": float(similarity),
            })
        return output

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]], user_id: int, document_id: int):
        ids = []
        documents = []
        metadata = []
        for i, chunk in enumerate(chunks):
            ids.append(f"{user_id}_{document_id}_{i}")
            documents.append(chunk["text"])
            metadata.append({
                "user_id": user_id,
                "document_id": document_id,
                "section": chunk.get("section", "unknown"),
            })
        self.collection.add(
            ids=ids,
            metadatas=metadata,
            documents=documents,
            embeddings=embeddings,
        )