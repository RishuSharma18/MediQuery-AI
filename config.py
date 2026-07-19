import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

DATABASE_PATH = "data/hospital.db"

VECTOR_DB_PATH = "vectorstore/faiss_index"