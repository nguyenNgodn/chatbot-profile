from ragchat.prompt_templates import RagPrompt


def test_prompt_includes_question_and_context():
    prompt = RagPrompt.build(
        context="Tên: Lan",
        history=[{"sender": "user", "content": "hi"}],
        question="Bạn tên gì?",
    )
    assert "Tên: Lan" in prompt
    assert "Bạn tên gì?" in prompt
    assert "Visitor: hi" in prompt
    assert "Không bịa" in prompt
    assert "Stylo" in prompt
