from src.models import HackathonConstraints
from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Optional
import os
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    temperature=0,
    model="gemini-2.5-flash",
)

parser = PydanticOutputParser(pydantic_object=HackathonConstraints)


class GraphState(TypedDict):
    raw_input: Optional[dict | str]
    constraints: Optional[HackathonConstraints]


def interpret_free_form(text: str) -> HackathonConstraints:
    prompt = f"""
Extract hackathon constraints from the text below.
If information is missing, choose conservative defaults.

Text:
{text}

Return JSON matching this schema exactly:
{HackathonConstraints.model_json_schema()}
"""
    print("Prompt sent to LLM:\n", prompt)

    raw = llm.invoke(prompt).content
    print("raw LLM output:\n", raw)
    constraints = parser.parse(raw)
    return constraints


def normalize_input(state: GraphState) -> GraphState:
    raw = state["raw_input"]
    if isinstance(raw, dict):
        constraints = HackathonConstraints.model_validate(raw)
    else:
        constraints = interpret_free_form(raw)

    return {**state, "constraints": constraints}


def main():
    print("Hello from hackathon-ideas-generator!")
    graph = StateGraph(GraphState)

    graph.add_node("normalize_input", normalize_input)
    graph.set_entry_point("normalize_input")
    graph.set_finish_point("normalize_input")

    constraint_graph = graph.compile()

    free_form_input = {
        "raw_input": (
            "48-hour student hackathon, teams of up to 4 people, "
            "medium difficulty, demo-focused, avoid big infra."
        )
    }

    result_1 = constraint_graph.invoke(free_form_input)
    print("\nFREE-FORM RESULT:\n", result_1["constraints"].model_dump())

    # ---- Example 2: structured input
    structured_input = {
        "raw_input": {
            "duration_hours": 36,
            "max_team_size": 4,
            "target_level": "mid-senior",
            "audience": "students",
            "soft_guidelines": ["Short hackathon", "Live demo required"],
            "forbidden_patterns": [
                "Large-scale distributed systems",
                "Long data collection pipelines",
            ],
        }
    }

    result_2 = constraint_graph.invoke(structured_input)
    print("\nSTRUCTURED RESULT:\n", result_2["constraints"].model_dump())


if __name__ == "__main__":
    main()
