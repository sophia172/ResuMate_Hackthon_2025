
import os
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
import getpass
from typing_extensions import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from typing_extensions import List, TypedDict


if not os.environ.get("GROQ_API_KEY"):
  os.environ["GROQ_API_KEY"] = getpass.getpass("Enter API key for Groq: ")



llm = init_chat_model("llama3-8b-8192", model_provider="groq")

# Schema for structured output to use as routing logic
class Route(BaseModel):
    step: Literal["CV", "Cover Letter", "Interview"] = Field(
        None, description="The next step in the routing process"
    )


# Augment the LLM with schema for structured output
router = llm.with_structured_output(Route)


# State
class State(TypedDict):
    input: str
    decision: str
    output: str
    person_context: str
    job_context: str


# Nodes
def generate_CoverLetter(state: State):
    """Write a Cover Letter"""

    prompt = f"""
                Here is the personal information:
                {state["person_context"]}.

                Here is the Job information:
                {state["job_context"]}

                Based on the following information, create a professional and detailed Cover Letter:

                Ensure the CV includes sections for:
                1. Header
                Your name, email, phone number, and optionally your LinkedIn profile.
                Date of submission.
                Hiring manager’s name, company, and address (if available).
                2. Salutation
                Address the hiring manager by name (e.g., Dear [Hiring Manager’s Name]).
                If the name isn’t available, use Dear Hiring Manager instead.
                3. Introduction
                Clearly state the position you're applying for.
                A compelling hook—why you're interested in the role or company.
                A sentence summarizing why you're a strong candidate.
                4. Body (1-2 paragraphs)
                Highlight relevant experience: Connect your skills and past achievements to the job requirements.
                Show enthusiasm for the company: Mention something specific about the company’s work or mission that excites you.
                Provide evidence: Use a brief example to demonstrate your skills in action.
                5. Closing Paragraph
                Express enthusiasm about the opportunity to discuss your qualifications further.
                Politely request an interview.
                Thank the reader for their time.
                6. Signature
                Sign off with Sincerely or Best regards, followed by your name.

                Format it in a clear and concise structure. No greetings, introductions, or unnecessary text.
                """
    result = llm.invoke(prompt)
    return {"output": result.content}


def Strike_Interview(state: State):
    """Write a Interview question"""

    result = llm.invoke(state["input"])
    return {"output": result.content}


def generate_CV(state: State):
    """Write a CV"""
    prompt = f"""
            Here is the personal information:
            {state["person_context"]}.

            Here is the Job information:
            {state["job_context"]}

            Based on the following information, create a professional and detailed CV:

            Ensure the CV includes sections for:
            - Personal Information
            - Professional Summary
            - Work Experience
            - Education
            - Skills
            - Certifications (if applicable)

            Format it in a clear and concise structure. No greetings, introductions, or unnecessary text.
            """
    result = llm.invoke(prompt)
    return {"output": result.content}


def llm_call_router(state: State):
    """Route the input to the appropriate node"""

    # Run the augmented LLM with structured output to serve as routing logic
    decision = router.invoke(
        [
            SystemMessage(
                content="Route the input to Cover Letter, Interview, or CV based on the user's request."
            ),
            HumanMessage(content=state["input"]),
        ]
    )

    return {"decision": decision.step}


# Conditional edge function to route to the appropriate node
def route_decision(state: State):
    # Return the node name you want to visit next
    if state["decision"] == "Cover Letter":
        return "generate_CoverLetter"
    elif state["decision"] == "Interview":
        return "Strike_Interview"
    elif state["decision"] == "CV":
        return "generate_CV"


# Build workflow
router_builder = StateGraph(State)

# Add nodes
router_builder.add_node("generate_CoverLetter", generate_CoverLetter)
router_builder.add_node("Strike_Interview", Strike_Interview)
router_builder.add_node("generate_CV", generate_CV)
router_builder.add_node("llm_call_router", llm_call_router)

# Add edges to connect nodes
router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {  # Name returned by route_decision : Name of next node to visit
        "generate_CoverLetter": "generate_CoverLetter",
        "Strike_Interview": "Strike_Interview",
        "generate_CV": "generate_CV",
    },
)
router_builder.add_edge("generate_CoverLetter", END)
router_builder.add_edge("Strike_Interview", END)
router_builder.add_edge("generate_CV", END)

# Compile workflow
router_workflow = router_builder.compile()



if __name__ == "__main__":
    state = router_workflow.invoke({
                 "input": "Give me a Cover Letter",
                 "job_context": "InstaDeep seeks a Lead Machine Learning Engineer to develop scalable, high-performance ML systems. You will optimize deep learning models, tackle performance bottlenecks, and design distributed infrastructure across GPUs/TPUs. This role involves technical leadership, hands-on coding in Python, C/C++, XLA, Triton, or CUDA, and collaboration with research and product teams. Responsibilities include algorithm optimization, distributed system design, automation of data pipelines, and mentoring engineers. You will drive the long-term roadmap for scalable AI systems while ensuring efficiency and best practices in model training and deployment.",
                 "person_context": "John Doe is a data professional with recent activity on LinkedIn. Their recent posts and engagements cover topics such as data analysis, machine learning, and industry trends. They also share insights on data visualization techniques and participate in discussions about the latest developments in data science.",
                    })
    print(state["output"])