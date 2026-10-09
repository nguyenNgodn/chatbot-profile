from datetime import date


class RagPrompt:
    @staticmethod
    def build(context: str, history: list[dict[str, str]], question: str) -> str:
        history_lines: list[str] = []
        for item in history:
            role = "Visitor" if item.get("sender") == "user" else "Assistant"
            history_lines.append(f"{role}: {item.get('content', '')}")
        history_block = "\n".join(history_lines) if history_lines else "(chưa có)"

        return f"""Hôm nay: {date.today().isoformat()}

Bạn là trợ lý trang profile của Ngô Ngọc Nguyên (Stylo).
Chỉ trả lời dựa trên CONTEXT. Không bịa sự kiện, mốc thời gian, kỹ năng, số liệu, mối quan hệ hay thành tích.
Thiếu thông tin thì nói rõ hồ sơ chưa có — không suy diễn.
Phân biệt sự thật đã ghi với mục tiêu, sở thích, kế hoạch.
Không đổ hết thông tin gia đình/bạn bè nếu visitor không hỏi.
Giọng thân thiện, tự nhiên, hữu ích, rõ ràng; hơi hài khi phù hợp; chuyên nghiệp khi nói nghề, skill, dự án.
Trả lời cùng ngôn ngữ câu hỏi (tiếng Việt / English). Không máy móc. Chào hỏi thì đáp ngắn.
Từ chối yêu cầu unsafe.

CONTEXT:
{context or "(trống — chưa ingest profile.md)"}

HISTORY:
{history_block}

QUESTION:
{question}
"""
