"""
Agents module for AI Finance Assistant.
Provides specialized agents for different financial domains.
"""

from src.agents.base_agent import BaseAgent
from src.agents.finance_qa_agent import FinanceQAAgent
from src.agents.portfolio_agent import PortfolioAnalysisAgent
from src.agents.market_agent import MarketAnalysisAgent
from src.agents.goal_planning_agent import GoalPlanningAgent
from src.agents.news_agent import NewsSynthesizerAgent

__all__ = [
    "BaseAgent",
    "FinanceQAAgent",
    "PortfolioAnalysisAgent",
    "MarketAnalysisAgent",
    "GoalPlanningAgent",
    "NewsSynthesizerAgent",
]
