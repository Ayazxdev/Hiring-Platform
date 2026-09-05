"""
LangGraph Workflow Definition

Connects all agents into a unified hiring pipeline.

Workflow:
START → verify_company (if score >= 60) → 
anonymize → portfolio_analysis (if weak) → 
test (optional) → aggregate → bias_detection (if no bias) → 
matching → passport → END
"""
import logging
from langgraph.graph import StateGraph, END

from state import HiringState
from nodes import (
    verify_company_node,
    anonymize_node,
    portfolio_analysis_node,
    skill_test_node,
    aggregate_skills_node,
    bias_detection_node,
    matching_node,
    passport_node,
    reject_node,
    should_proceed_after_company,
    should_require_test,
    check_bias_status
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_hiring_workflow() -> StateGraph:
    """
    Create the complete hiring workflow graph
    
    Returns:
        Compiled LangGraph StateGraph
    """
    logger.info("Building Fair Hiring workflow graph...")
    
    # Initialize graph with state schema
    graph = StateGraph(HiringState)
    
    # ADD NODES
    graph.add_node("verify_company", verify_company_node)
    graph.add_node("reject", reject_node)
    graph.add_node("anonymize", anonymize_node)
    graph.add_node("portfolio_analysis", portfolio_analysis_node)
    graph.add_node("skill_test", skill_test_node)
    graph.add_node("aggregate_skills", aggregate_skills_node)
    graph.add_node("bias_detection", bias_detection_node)
    graph.add_node("matching", matching_node)
    graph.add_node("passport", passport_node)
    
    # SET ENTRY POINT
    graph.set_entry_point("verify_company")
    
    # ADD EDGES
    
    # 1. After company verification: proceed or reject
    graph.add_conditional_edges(
        "verify_company",
        should_proceed_after_company,
        {
            "continue": "anonymize",
            "reject": "reject"
        }
    )
    
    # 2. Reject goes to END
    graph.add_edge("reject", END)
    
    # 3. After anonymize: portfolio analysis
    graph.add_edge("anonymize", "portfolio_analysis")
    
    # 4. After portfolio: decide if test needed
    graph.add_conditional_edges(
        "portfolio_analysis",
        should_require_test,
        {
            "skip_test": "aggregate_skills",
            "require_test": "skill_test"
        }
    )
    
    # 5. After test: aggregate
    graph.add_edge("skill_test", "aggregate_skills")
    
    # 6. After aggregate: bias detection
    graph.add_edge("aggregate_skills", "bias_detection")
    
    # 7. After bias detection: check status
    graph.add_conditional_edges(
        "bias_detection",
        check_bias_status,
        {
            "proceed": "matching",
            "review": "matching"  # Still proceed but with alert published
        }
    )
    
    # 8. After matching: issue passport
    graph.add_edge("matching", "passport")
    
    # 9. Passport is the final node
    graph.add_edge("passport", END)
    
    logger.info("Workflow graph built successfully")
    
    # Compile and return
    return graph.compile()


# Create the compiled workflow
workflow = create_hiring_workflow()
