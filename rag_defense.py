import chromadb
client = chromadb.Client()

collection = client.get_or_create_collection(
    name="my_collection"
)

# Add documents
collection.add(
    ids=["id1", "id2"],
    documents=["Database systems", "Machine learning"]
)

# Full-text search
results = collection.get(
    where_document={"$contains": "database"}
)

# Regex search
regex_results = collection.get(
    where_document={
       "$regex": "^data.*"
   }
)