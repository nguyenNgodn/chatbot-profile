from config import ROOT_DIR

COLLECTION_NAME = "profile_kb"
CHROMA_DIR = ROOT_DIR / "chroma_storage"
DATA_DIR = ROOT_DIR / "data"
EMBED_MODEL_NAME = "AITeamVN/Vietnamese_Embedding"
CHUNKING = "semantic"
TOP_K = 5
HISTORY_FOR_PROMPT = 10
MESSAGE_TRIM = 20
RETRIEVAL_CACHE_TTL = 300
LLM_CACHE_TTL = 300
GEMINI_MODEL = "gemini-3.5-flash-lite"

CHATBOT_FIRST_MESSAGE = (
    "Xin chào! Mình có thể giúp bạn tìm hiểu về chủ nhân trang profile này."
)

LLM_FALLBACK = (
    "Xin lỗi, mình chưa trả lời được lúc này. Bạn thử hỏi lại sau giúp mình nhé."
)
