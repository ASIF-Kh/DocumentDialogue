import chromadb

# Connect to persistent ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
print(client.list_collections())
# # List and delete all collections
for collection in client.list_collections():
    print(f"Deleting collection: {collection.name}")
#     client.delete_collection(name=collection.name)
