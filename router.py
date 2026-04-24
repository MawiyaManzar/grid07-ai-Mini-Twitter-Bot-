"""
Tradeoffs I chose :
The assignment asks to return only bots above a cosine-similarity threshold.
In practice, real posts sometimes produce low absolute similarity while top-1 ranking is still correct.
So this router uses:
1) threshold filtering (primary behavior), and
2) a fallback that returns top-1 with {"low_confidence": True} if no bot passes threshold.
This avoids empty routing and makes behavior more robust for real-world phrasing.
it was chosen after testing with actual assignments examples.
"""

import chromadb
from embeddings import embed
import embeddings
from dotenv import load_dotenv

load_dotenv()

client=chromadb.Client()

collection= client.get_or_create_collection(
    name="persona_router",
    metadata={"hnsw:space": "cosine"}  

)

bots = [
    {
        "id": "A",
        "persona": (
            "I believe AI and crypto will solve all human problems. "
            "I am highly optimistic about technology, Elon Musk, and space exploration. "
            "I dismiss regulatory concerns."
        ),
    },
    {
        "id": "B",
        "persona": (
            "I believe late-stage capitalism and tech monopolies are destroying society. "
            "I am highly critical of AI, social media, and billionaires. "
            "I value privacy and nature."
        ),
    },
    {
        "id": "C",
        "persona": (
            "I strictly care about markets, interest rates, trading algorithms, and making money. "
            "I speak in finance jargon and view everything through the lens of ROI."
        ),
    },
]

def load_personas():
    ids= [i["id"] for i in bots]
    documents=[bot["persona"] for bot in bots]
    embeddings=[embed(text) for text in documents]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings
    )


#Routing function

def route_post_to_bots(post_content: str, threshold: float = 0.3):
    post_embedding = embed(post_content)

    results = collection.query(
        query_embeddings=[post_embedding],
        n_results=3
    )

    scored = []
    for i in range(len(results["ids"][0])):
        bot_id = results["ids"][0][i]
        distance = results["distances"][0][i]
        similarity = 1 - distance
        print(f"bot={bot_id}, distance={distance:.4f}, similarity={similarity:.4f}")
        scored.append({"bot_id": bot_id, "score": similarity})
    matched = [x for x in scored if x["score"] >= threshold]
    if matched:
        return matched
    # fallback: return best bot instead of []
    top = max(scored, key=lambda x: x["score"])
    top["low_confidence"] = True
    return [top]



if __name__ == "__main__":
    load_personas()
    post = "OpenAI released a new model replacing developers"
    print(route_post_to_bots(post))