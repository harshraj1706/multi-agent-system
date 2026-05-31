from agent import AgentRunner, _message_text
from langchain_core.messages import AIMessage
from tool import extract_main_content


class FakeAgentGraph:
    def invoke(self, inputs, config=None):
        return {"messages": [AIMessage(content="pipeline smoke test ok")]}


def test_agent_runner_output_shape():
    runner = AgentRunner(FakeAgentGraph())
    result = runner.invoke({"input": "hello"})
    assert result["output"] == "pipeline smoke test ok"
    assert result["messages"]


def test_message_text_handles_string_content():
    assert _message_text(AIMessage(content="hello")) == "hello"


def test_extract_main_content_rejects_empty_url():
    assert "missing URL" in extract_main_content("")


if __name__ == "__main__":
    test_agent_runner_output_shape()
    test_message_text_handles_string_content()
    test_extract_main_content_rejects_empty_url()
    print("All smoke tests passed.")
