import logging
from langgraph.graph import StateGraph, END
from app.agent.state import RecoveryAgentState
from app.agent.nodes import (
    diagnose_and_score_node,
    policy_check_node,
    execute_action_node
)

logger = logging.getLogger("recoverai.agent_graph")


def build_recovery_graph():
    """
    Builds and compiles the LangGraph StateGraph workflow:
    START -> Diagnose & Score -> Policy Check -> Execute Action -> END
    """
    workflow = StateGraph(RecoveryAgentState)

    # Add nodes
    workflow.add_node("diagnose_and_score", diagnose_and_score_node)
    workflow.add_node("policy_check", policy_check_node)
    workflow.add_node("execute_action", execute_action_node)

    # Set entry point
    workflow.set_entry_point("diagnose_and_score")

    # Add linear transitions
    workflow.add_edge("diagnose_and_score", "policy_check")
    workflow.add_edge("policy_check", "execute_action")
    workflow.add_edge("execute_action", END)

    return workflow.compile()


recovery_agent_graph = build_recovery_graph()
