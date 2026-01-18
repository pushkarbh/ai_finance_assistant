"""
Goal Planning Agent for AI Finance Assistant.
Assists with financial goal setting and projections.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import math

from src.agents.base_agent import BaseAgent
from src.core.state import AgentState, update_state_with_agent_output, FinancialGoal
from src.core.llm import AGENT_SYSTEM_PROMPTS


class GoalPlanningAgent(BaseAgent):
    """
    Goal Planning Agent.
    Helps users set financial goals, create plans, and understand
    projections with educational context.
    """

    # Standard return assumptions for projections
    RETURN_ASSUMPTIONS = {
        'conservative': 0.04,  # 4% - mostly bonds
        'moderate': 0.06,      # 6% - balanced
        'aggressive': 0.08,    # 8% - mostly stocks
        'historical_avg': 0.07  # 7% - common planning assumption
    }

    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the Goal Planning Agent.

        Args:
            system_prompt: Custom system prompt
        """
        super().__init__(
            name="Goal Planning Agent",
            description="Assists with financial goal setting and projections",
            system_prompt=system_prompt or AGENT_SYSTEM_PROMPTS["goal_planning"]
        )

    def process(self, state: AgentState) -> AgentState:
        """
        Process goal planning request.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        query = state["current_query"]
        goals = state.get("goals", [])
        portfolio = state.get("portfolio")

        # Extract goal parameters from query if possible
        goal_params = self._extract_goal_params(query)

        # Generate response based on available information
        if goal_params:
            response = self.create_goal_plan(goal_params, portfolio)
        else:
            response = self.provide_goal_guidance(query, goals, portfolio)

        state = update_state_with_agent_output(state, "goal_planning", {
            "response": response,
            "goal_params": goal_params,
            "projections_generated": bool(goal_params)
        })

        return state

    def _extract_goal_params(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Extract goal parameters from a query.

        Args:
            query: User's query

        Returns:
            Dict with goal parameters if found
        """
        # Use LLM to extract goal parameters
        extract_prompt = f"""Extract financial goal parameters from this query if present:

Query: {query}

If the query contains a specific financial goal, extract:
- goal_type: (retirement, house, education, emergency, general)
- target_amount: (number if specified)
- current_savings: (number if specified)
- monthly_contribution: (number if specified)
- years_to_goal: (number if specified)
- risk_tolerance: (conservative, moderate, aggressive)

Respond in this format (use "none" if not specified):
GOAL_TYPE: <type or none>
TARGET_AMOUNT: <number or none>
CURRENT_SAVINGS: <number or none>
MONTHLY_CONTRIBUTION: <number or none>
YEARS_TO_GOAL: <number or none>
RISK_TOLERANCE: <level or none>

If this is not a goal-planning query, respond with just: NOT_GOAL_QUERY"""

        response = self.generate_response(extract_prompt)

        if "NOT_GOAL_QUERY" in response:
            return None

        params = {}
        for line in response.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip().lower()

                if value != 'none':
                    # Convert numeric values
                    if key in ['target_amount', 'current_savings', 'monthly_contribution']:
                        try:
                            # Remove common formatting
                            value = value.replace('$', '').replace(',', '').replace('k', '000').replace('m', '000000')
                            params[key] = float(value)
                        except ValueError:
                            pass
                    elif key == 'years_to_goal':
                        try:
                            params[key] = int(float(value))
                        except ValueError:
                            pass
                    else:
                        params[key] = value

        return params if params else None

    def create_goal_plan(
        self,
        params: Dict[str, Any],
        portfolio: Optional[Dict] = None
    ) -> str:
        """
        Create a detailed goal plan with projections.

        Args:
            params: Goal parameters
            portfolio: Optional current portfolio

        Returns:
            Educational goal plan
        """
        goal_type = params.get('goal_type', 'general')
        target_amount = params.get('target_amount', 0)
        current_savings = params.get('current_savings', 0)
        monthly_contribution = params.get('monthly_contribution', 0)
        years_to_goal = params.get('years_to_goal', 0)
        risk_tolerance = params.get('risk_tolerance', 'moderate')

        # Generate projections
        projections = {}
        if target_amount and years_to_goal:
            projections = self.calculate_projections(
                target_amount=target_amount,
                current_savings=current_savings,
                monthly_contribution=monthly_contribution,
                years=years_to_goal,
                risk_tolerance=risk_tolerance
            )
        elif target_amount and monthly_contribution:
            projections = self.calculate_time_to_goal(
                target_amount=target_amount,
                current_savings=current_savings,
                monthly_contribution=monthly_contribution,
                risk_tolerance=risk_tolerance
            )

        # Format projection data
        projection_text = self._format_projections(projections)

        # Get goal-specific guidance
        goal_guidance = self._get_goal_type_guidance(goal_type)

        # Format parameter values for display
        target_str = f"${target_amount:,.2f}" if target_amount else "Not specified"
        current_str = f"${current_savings:,.2f}" if current_savings else "Not specified"
        monthly_str = f"${monthly_contribution:,.2f}" if monthly_contribution else "Not specified"
        years_str = f"{years_to_goal} years" if years_to_goal else "Not specified"

        prompt = f"""Create an educational financial goal plan based on these parameters:

GOAL PARAMETERS:
- Goal Type: {goal_type}
- Target Amount: {target_str}
- Current Savings: {current_str}
- Monthly Contribution: {monthly_str}
- Time Horizon: {years_str}
- Risk Tolerance: {risk_tolerance}

PROJECTIONS:
{projection_text}

GOAL-SPECIFIC CONSIDERATIONS:
{goal_guidance}

Please provide:
1. Analysis of their goal feasibility
2. Explanation of the projections (what assumptions mean)
3. Suggestions to improve their plan
4. Important considerations and risks
5. Next steps they might consider

Be encouraging but realistic. Explain the math simply."""

        return self.generate_response(prompt)

    def calculate_projections(
        self,
        target_amount: float,
        current_savings: float,
        monthly_contribution: float,
        years: int,
        risk_tolerance: str = 'moderate'
    ) -> Dict[str, Any]:
        """
        Calculate investment projections.

        Args:
            target_amount: Goal amount
            current_savings: Current savings
            monthly_contribution: Monthly contribution
            years: Years until goal
            risk_tolerance: Risk tolerance level

        Returns:
            Projection results
        """
        rate = self.RETURN_ASSUMPTIONS.get(risk_tolerance, 0.07)
        monthly_rate = rate / 12
        months = years * 12

        # Future value calculation
        # FV = PV * (1 + r)^n + PMT * [((1 + r)^n - 1) / r]
        if monthly_rate > 0:
            fv_current = current_savings * ((1 + monthly_rate) ** months)
            fv_contributions = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        else:
            fv_current = current_savings
            fv_contributions = monthly_contribution * months

        projected_total = fv_current + fv_contributions
        total_contributions = current_savings + (monthly_contribution * months)
        investment_growth = projected_total - total_contributions

        # Calculate required monthly to reach goal
        if target_amount > fv_current and months > 0 and monthly_rate > 0:
            remaining_needed = target_amount - fv_current
            required_monthly = remaining_needed * monthly_rate / (((1 + monthly_rate) ** months - 1))
        else:
            required_monthly = 0

        # Calculate probability scenarios
        scenarios = self._calculate_scenarios(
            current_savings, monthly_contribution, years, target_amount
        )

        return {
            'target_amount': target_amount,
            'projected_total': projected_total,
            'total_contributions': total_contributions,
            'investment_growth': investment_growth,
            'assumed_return': rate * 100,
            'will_reach_goal': projected_total >= target_amount,
            'surplus_or_shortfall': projected_total - target_amount,
            'required_monthly': required_monthly,
            'current_monthly': monthly_contribution,
            'scenarios': scenarios
        }

    def _calculate_scenarios(
        self,
        current: float,
        monthly: float,
        years: int,
        target: float
    ) -> Dict[str, float]:
        """Calculate different return scenarios."""
        scenarios = {}
        for name, rate in self.RETURN_ASSUMPTIONS.items():
            monthly_rate = rate / 12
            months = years * 12

            if monthly_rate > 0:
                fv_current = current * ((1 + monthly_rate) ** months)
                fv_contrib = monthly * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            else:
                fv_current = current
                fv_contrib = monthly * months

            scenarios[name] = {
                'projected': fv_current + fv_contrib,
                'rate': rate * 100,
                'reaches_goal': (fv_current + fv_contrib) >= target
            }

        return scenarios

    def calculate_time_to_goal(
        self,
        target_amount: float,
        current_savings: float,
        monthly_contribution: float,
        risk_tolerance: str = 'moderate'
    ) -> Dict[str, Any]:
        """
        Calculate how long to reach a goal.

        Args:
            target_amount: Goal amount
            current_savings: Current savings
            monthly_contribution: Monthly contribution
            risk_tolerance: Risk tolerance level

        Returns:
            Time projection results
        """
        rate = self.RETURN_ASSUMPTIONS.get(risk_tolerance, 0.07)
        monthly_rate = rate / 12

        if monthly_contribution <= 0 or target_amount <= current_savings:
            return {
                'target_amount': target_amount,
                'already_reached': target_amount <= current_savings,
                'needs_contributions': True
            }

        # Solve for n: FV = PV(1+r)^n + PMT[((1+r)^n - 1)/r]
        # This requires numerical approximation
        months = 0
        current_value = current_savings
        max_months = 600  # 50 years cap

        while current_value < target_amount and months < max_months:
            current_value = current_value * (1 + monthly_rate) + monthly_contribution
            months += 1

        years = months / 12

        return {
            'target_amount': target_amount,
            'current_savings': current_savings,
            'monthly_contribution': monthly_contribution,
            'months_to_goal': months,
            'years_to_goal': years,
            'assumed_return': rate * 100,
            'total_contributions': current_savings + (monthly_contribution * months),
            'final_value': current_value
        }

    def _format_projections(self, projections: Dict[str, Any]) -> str:
        """Format projections for display."""
        if not projections:
            return "No projections calculated (missing parameters)"

        lines = []

        if 'projected_total' in projections:
            lines.append(f"Projected Final Amount: ${projections['projected_total']:,.2f}")
            lines.append(f"Target Amount: ${projections['target_amount']:,.2f}")
            lines.append(f"Surplus/Shortfall: ${projections['surplus_or_shortfall']:,.2f}")
            lines.append(f"Total Contributions: ${projections['total_contributions']:,.2f}")
            lines.append(f"Investment Growth: ${projections['investment_growth']:,.2f}")
            lines.append(f"Assumed Annual Return: {projections['assumed_return']:.1f}%")

            if projections.get('required_monthly', 0) > 0:
                lines.append(f"Required Monthly to Reach Goal: ${projections['required_monthly']:,.2f}")

            if 'scenarios' in projections:
                lines.append("\nScenarios:")
                for name, scenario in projections['scenarios'].items():
                    status = "✓ Reaches goal" if scenario['reaches_goal'] else "✗ Falls short"
                    lines.append(
                        f"  {name.title()} ({scenario['rate']:.0f}%): "
                        f"${scenario['projected']:,.2f} - {status}"
                    )

        elif 'years_to_goal' in projections:
            lines.append(f"Time to Reach Goal: {projections['years_to_goal']:.1f} years")
            lines.append(f"({projections['months_to_goal']} months)")
            lines.append(f"Assumed Annual Return: {projections['assumed_return']:.1f}%")

        return '\n'.join(lines)

    def _get_goal_type_guidance(self, goal_type: str) -> str:
        """Get goal-specific educational guidance."""
        guidance = {
            'retirement': """
- Consider tax-advantaged accounts (401k, IRA)
- Factor in Social Security estimates
- Plan for 25-30 years of retirement
- Healthcare costs are significant
- The 4% rule is a common withdrawal guideline""",

            'house': """
- Typical down payment is 20% to avoid PMI
- Budget for closing costs (2-5%)
- Consider total housing costs, not just mortgage
- Emergency fund should remain intact
- Location significantly impacts affordability""",

            'education': """
- 529 plans offer tax advantages
- Consider tuition inflation (historically 5-8%)
- Look into scholarships and financial aid
- Room and board add significantly to costs
- Start early for maximum compound growth""",

            'emergency': """
- Target 3-6 months of expenses
- Keep in easily accessible accounts
- High-yield savings accounts are appropriate
- Don't invest emergency funds in stocks
- Rebuild immediately after using""",

            'general': """
- Define specific, measurable goals
- Set realistic timelines
- Consider opportunity cost
- Build emergency fund first
- Review and adjust plans regularly"""
        }

        return guidance.get(goal_type, guidance['general'])

    def provide_goal_guidance(
        self,
        query: str,
        goals: List[Dict],
        portfolio: Optional[Dict]
    ) -> str:
        """
        Provide general goal planning guidance.

        Args:
            query: User's query
            goals: Existing goals if any
            portfolio: Portfolio if available

        Returns:
            Educational guidance
        """
        context = ""
        if goals:
            context += f"\nExisting Goals: {len(goals)} goals defined"
        if portfolio:
            context += f"\nPortfolio Value: ${portfolio.get('total_value', 0):,.2f}"

        prompt = f"""Provide educational guidance for this goal planning question:

USER QUESTION: {query}
{context}

Please provide:
1. Answer to their specific question
2. Educational context about goal planning
3. Key factors to consider
4. Suggested next steps

Be helpful and educational. If they need to provide more information for detailed projections, explain what would be helpful."""

        return self.generate_response(prompt)
