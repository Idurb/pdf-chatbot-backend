# # import faiss
# # import numpy as np

# # dimension = 384  # depends on model
# # index = faiss.IndexFlatL2(dimension)

# # # Store mapping
# # chunk_store = []

# # def add_embeddings(embeddings, chunks):
# #     global chunk_store

# #     vectors = np.array(embeddings).astype("float32")
# #     index.add(vectors)

# #     chunk_store.extend(chunks)


# # def search(query_embedding, top_k=3):
# #     query_vector = np.array([query_embedding]).astype("float32")
# #     distances, indices = index.search(query_vector, top_k)

# #     results = [chunk_store[i] for i in indices[0]]
# #     return results
# # def reset_index():
# #     global index, chunk_store
# #     index.reset()
# #     chunk_store = []
# import faiss
# import numpy as np

# dimension = 384
# index = faiss.IndexFlatL2(dimension)

# chunk_store = []


# def reset_index():
#     global index, chunk_store
#     index.reset()
#     chunk_store = []


# def add_embeddings(embeddings, chunks):
#     global chunk_store

#     vectors = np.array(embeddings).astype("float32")
#     index.add(vectors)

#     chunk_store.extend(chunks)


# def search(query_embedding, top_k=5):
#     query_vector = np.array([query_embedding]).astype("float32")
#     distances, indices = index.search(query_vector, top_k)

#     results = []

#     for i in indices[0]:
#         if 0 <= i < len(chunk_store):
#             results.append(chunk_store[i])

#     return results
import faiss
import numpy as np

dimension = 384
index = faiss.IndexFlatL2(dimension)

chunk_store = []

def reset_index():
    global index, chunk_store
    index.reset()
    chunk_store = []

def add_embeddings(embeddings, chunks):
    global chunk_store

    vectors = np.array(embeddings).astype("float32")
    index.add(vectors)

    chunk_store.extend(chunks)

def search(query_embedding, top_k=5):
    query_vector = np.array([query_embedding]).astype("float32")
    distances, indices = index.search(query_vector, top_k)

    results = []

    for i in indices[0]:
        if 0 <= i < len(chunk_store):
            results.append(chunk_store[i])

    return results