"""Ask the stored CV a question and see which chunks come back, nearest first.

    python chatbot/src/probe.py "What did you do at Entain?"
    python chatbot/src/probe.py            # runs the built-in recruiter questions

Not part of the chatbot: it is a way to judge retrieval quality by eye before the LLM
is involved. Distance is cosine distance: 0 = identical direction, bigger = less related.
"""
import sys

import chromadb

from indexing import COLLECTION, DB_DIR, embedding_function

QUESTIONS = [
    "What did you do at Entain?",
    "What did you do at Reality AI Lab?",
    "Where are you based and how can I contact you?",
    "Do you have cloud experience?",
    "Have you used Docker?",
    "Tell me about your machine learning projects",
    "Have you built anything with real-time collaboration?",
    "Have you built mobile apps?",
    "What is your degree?",
    "What programming languages do you know?",
    "Do you have any certifications?",
    "Are you good at working in a team or leading people?",
]


def retrieve(question, k=3, db_dir=DB_DIR):
    client = chromadb.PersistentClient(path=str(db_dir))
    collection = client.get_collection(COLLECTION, embedding_function=embedding_function())
    result = collection.query(query_texts=[question], n_results=k)
    return [
        {"id": id_, "distance": distance, **metadata}
        for id_, distance, metadata in zip(result["ids"][0], result["distances"][0], result["metadatas"][0])
    ]


def main(argv=None):
    questions = (sys.argv[1:] if argv is None else argv) or QUESTIONS
    for question in questions:
        print(f"\nQ: {question}")
        for rank, hit in enumerate(retrieve(question), start=1):
            print(f"   {rank}. {hit['distance']:.3f}  {hit['title']}  [{hit['kind']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
