"""
Portfolio Analysis Agent for AI Finance Assistant.
Analyzes user portfolios and provides educational insights.
"""

import pandas as pd
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.core.state import AgentState, update_state_with_agent_output, PortfolioHolding
from src.core.llm import AGENT_SYSTEM_PROMPTS
from src.utils.market_data import get_stock_price, get_stock_info, get_multiple_prices


class PortfolioAnalysisAgent(BaseAgent):
    """
    Portfolio Analysis Agent.
    Analyzes investment portfolios and provides educational insights about
    allocation, diversification, risk, and performance.
    """

    def __init__(self, system_prompt: Optional[str] = None):
        """
        Initialize the Portfolio Analysis Agent.

        Args:
            system_prompt: Custom system prompt
        """
        super().__init__(
            name="Portfolio Analysis Agent",
            description="Reviews and analyzes user portfolios with educational insights",
            system_prompt=system_prompt or AGENT_SYSTEM_PROMPTS["portfolio_analysis"]
        )

    def process(self, state: AgentState) -> AgentState:
        """
        Process portfolio analysis request.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        query = state["current_query"]
        portfolio_data = state.get("portfolio")

        if not portfolio_data:
            # No portfolio provided, give general guidance
            response = self.generate_response(
                f"The user asked about portfolio analysis but hasn't provided portfolio data: {query}\n\n"
                "Please provide guidance on how to share their portfolio for analysis, "
                "or answer general portfolio questions."
            )
            state = update_state_with_agent_output(state, "portfolio_analysis", {
                "response": response,
                "portfolio_provided": False
            })
            return state

        # Analyze the portfolio
        analysis = self.analyze_portfolio(portfolio_data)

        # Generate insights based on query
        response = self.generate_portfolio_insights(query, analysis)

        state = update_state_with_agent_output(state, "portfolio_analysis", {
            "response": response,
            "analysis": analysis,
            "portfolio_provided": True
        })

        return state

    def parse_portfolio_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse portfolio data from CSV content.

        Args:
            csv_content: CSV string with portfolio data

        Returns:
            List of holdings dictionaries
        """
        import io
        df = pd.read_csv(io.StringIO(csv_content))

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        # Map common column names
        column_mapping = {
            'symbol': 'ticker',
            'stock': 'ticker',
            'quantity': 'shares',
            'qty': 'shares',
            'units': 'shares',
            'cost': 'purchase_price',
            'cost_basis': 'purchase_price',
            'buy_price': 'purchase_price',
            'date': 'purchase_date',
            'buy_date': 'purchase_date'
        }

        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)

        holdings = []
        for _, row in df.iterrows():
            holding = {
                'type': 'stock',  # CSV imports are assumed to be stocks
                'ticker': row.get('ticker', '').upper(),
                'shares': float(row.get('shares', 0)),
                'purchase_price': float(row.get('purchase_price', 0)) if pd.notna(row.get('purchase_price')) else None,
                'purchase_date': row.get('purchase_date') if pd.notna(row.get('purchase_date')) else None
            }
            if holding['ticker'] and holding['shares'] > 0:
                holdings.append(holding)

        return holdings

    def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive portfolio analysis.

        Args:
            portfolio_data: Portfolio data dictionary

        Returns:
            Analysis results dictionary
        """
        holdings = portfolio_data.get('holdings', [])

        if not holdings:
            return {"error": "No holdings found in portfolio"}

        # Normalize holdings - add 'type' field for backward compatibility
        for h in holdings:
            if 'type' not in h:
                # If it has a ticker, it's a stock
                if 'ticker' in h and h['ticker']:
                    h['type'] = 'stock'
                else:
                    h['type'] = 'other'

        # Separate stock and non-stock holdings
        stock_holdings = [h for h in holdings if h.get('type') == 'stock']
        non_stock_holdings = [h for h in holdings if h.get('type') != 'stock']

        # Get current prices for stock tickers
        tickers = [h.get('ticker') for h in stock_holdings if h.get('ticker')]
        current_prices = get_multiple_prices(tickers) if tickers else {}

        # Calculate values and metrics
        total_value = 0
        total_cost = 0
        analyzed_holdings = []
        sector_allocation = {}
        asset_type_allocation = {}

        # Process stock holdings
        for holding in stock_holdings:
            ticker = holding.get('ticker')
            if not ticker:
                continue
                
            shares = holding.get('shares', 0)
            purchase_price = holding.get('purchase_price', 0)

            # Get current price
            current_price = current_prices.get(ticker, {}).get('price', 0)
            stock_info = get_stock_info(ticker)

            # Calculate values
            current_value = shares * current_price
            cost_basis = shares * purchase_price if purchase_price else 0
            gain_loss = current_value - cost_basis if cost_basis else 0
            gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis else 0

            total_value += current_value
            total_cost += cost_basis

            # Track sector allocation
            sector = stock_info.get('sector', 'Unknown')
            sector_allocation[sector] = sector_allocation.get(sector, 0) + current_value

            # Track asset type (simplified)
            asset_type = self._classify_asset_type(ticker, stock_info)
            asset_type_allocation[asset_type] = asset_type_allocation.get(asset_type, 0) + current_value

            analyzed_holdings.append({
                'ticker': ticker,
                'shares': shares,
                'purchase_price': purchase_price,
                'current_price': current_price,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'gain_loss': gain_loss,
                'gain_loss_pct': gain_loss_pct,
                'sector': sector,
                'company_name': stock_info.get('name', ticker)
            })
        
        # Process non-stock holdings (bonds, cash, CDs, etc.)
        for holding in non_stock_holdings:
            inv_type = holding.get('type', 'other')
            name = holding.get('name', 'Unknown')
            amount = holding.get('shares', 0)  # For non-stocks, shares = dollar amount
            yield_rate = holding.get('purchase_price', 0)  # For non-stocks, purchase_price = yield/rate
            
            # For non-stocks, current value = amount (no price appreciation)
            current_value = amount
            cost_basis = amount
            gain_loss = 0  # No capital gains for cash/bonds (only interest)
            gain_loss_pct = 0
            
            total_value += current_value
            total_cost += cost_basis
            
            # Track as separate asset type
            type_name_map = {
                'bond': 'Bonds',
                'cash': 'Cash & Equivalents',
                'cd': 'Certificates of Deposit',
                'other': 'Other Investments'
            }
            asset_type = type_name_map.get(inv_type, 'Other Investments')
            asset_type_allocation[asset_type] = asset_type_allocation.get(asset_type, 0) + current_value
            
            # Add to sector allocation as "Fixed Income" or "Cash"
            sector = 'Cash & Equivalents' if inv_type == 'cash' else 'Fixed Income'
            sector_allocation[sector] = sector_allocation.get(sector, 0) + current_value
            
            analyzed_holdings.append({
                'ticker': name,  # Use name instead of ticker
                'shares': 1,  # Not applicable
                'purchase_price': amount,  # Show amount
                'current_price': amount,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'gain_loss': gain_loss,
                'gain_loss_pct': gain_loss_pct,
                'sector': sector,
                'company_name': f"{asset_type} - {name}",
                'investment_type': inv_type,
                'yield_rate': yield_rate
            })

        # Calculate allocation percentages
        sector_pct = {k: (v / total_value * 100) if total_value else 0 for k, v in sector_allocation.items()}
        asset_type_pct = {k: (v / total_value * 100) if total_value else 0 for k, v in asset_type_allocation.items()}

        # Calculate portfolio metrics
        total_gain_loss = total_value - total_cost if total_cost else 0
        total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost else 0

        # Calculate diversification score (simplified)
        diversification_score = self._calculate_diversification_score(sector_pct, len(holdings))

        return {
            'holdings': analyzed_holdings,
            'total_value': total_value,
            'total_cost': total_cost,
            'total_gain_loss': total_gain_loss,
            'total_gain_loss_pct': total_gain_loss_pct,
            'num_holdings': len(holdings),
            'sector_allocation': sector_pct,
            'asset_type_allocation': asset_type_pct,
            'diversification_score': diversification_score,
            'analysis_date': datetime.now().isoformat()
        }

    def _classify_asset_type(self, ticker: str, stock_info: Dict) -> str:
        """Classify holding into asset type."""
        ticker_upper = ticker.upper()

        # Check for common ETF patterns
        if any(etf in ticker_upper for etf in ['SPY', 'VOO', 'VTI', 'IVV', 'QQQ']):
            return 'US Stock ETF'
        elif any(etf in ticker_upper for etf in ['VXUS', 'VEA', 'VWO', 'EFA']):
            return 'International ETF'
        elif any(etf in ticker_upper for etf in ['BND', 'AGG', 'TLT', 'VBTLX']):
            return 'Bond ETF'
        elif any(etf in ticker_upper for etf in ['VNQ', 'SCHH']):
            return 'REIT ETF'
        elif stock_info.get('quoteType') == 'ETF':
            return 'ETF'
        else:
            return 'Individual Stock'

    def _calculate_diversification_score(
        self,
        sector_allocation: Dict[str, float],
        num_holdings: int
    ) -> Dict[str, Any]:
        """
        Calculate a simple diversification score.

        Args:
            sector_allocation: Sector allocation percentages
            num_holdings: Number of holdings

        Returns:
            Diversification assessment
        """
        # Check for concentration
        max_sector_pct = max(sector_allocation.values()) if sector_allocation else 100
        num_sectors = len([s for s in sector_allocation.values() if s > 1])

        # Score components
        holding_score = min(num_holdings / 10, 1) * 30  # Max 30 points for 10+ holdings
        sector_score = min(num_sectors / 5, 1) * 30  # Max 30 points for 5+ sectors
        concentration_score = max(0, 40 - (max_sector_pct - 20))  # Penalize if >20% in one sector

        total_score = holding_score + sector_score + concentration_score

        if total_score >= 80:
            rating = "Well Diversified"
        elif total_score >= 60:
            rating = "Moderately Diversified"
        elif total_score >= 40:
            rating = "Somewhat Concentrated"
        else:
            rating = "Highly Concentrated"

        return {
            'score': round(total_score, 1),
            'rating': rating,
            'num_holdings': num_holdings,
            'num_sectors': num_sectors,
            'max_sector_concentration': round(max_sector_pct, 1)
        }

    def generate_portfolio_insights(
        self,
        query: str,
        analysis: Dict[str, Any]
    ) -> str:
        """
        Generate educational insights based on portfolio analysis.

        Args:
            query: User's original query
            analysis: Portfolio analysis results

        Returns:
            Educational response with insights
        """
        # Format analysis data for the prompt
        analysis_summary = f"""
PORTFOLIO SUMMARY:
- Total Value: ${analysis['total_value']:,.2f}
- Total Cost Basis: ${analysis['total_cost']:,.2f}
- Total Gain/Loss: ${analysis['total_gain_loss']:,.2f} ({analysis['total_gain_loss_pct']:.1f}%)
- Number of Holdings: {analysis['num_holdings']}

DIVERSIFICATION:
- Score: {analysis['diversification_score']['score']}/100 ({analysis['diversification_score']['rating']})
- Number of Sectors: {analysis['diversification_score']['num_sectors']}
- Largest Sector Concentration: {analysis['diversification_score']['max_sector_concentration']:.1f}%

SECTOR ALLOCATION:
{self._format_allocation(analysis['sector_allocation'])}

HOLDINGS:
{self._format_holdings(analysis['holdings'][:10])}  # Top 10 holdings
"""

        prompt = f"""Based on the following portfolio analysis, provide educational insights for the user.

{analysis_summary}

USER QUESTION: {query}

Please provide:
1. Direct answer to their question
2. Key observations about their portfolio
3. Educational context (what these metrics mean)
4. Suggestions for consideration (educational, not advice)

Be encouraging and educational. Explain any financial terms used."""

        return self.generate_response(prompt)

    def _format_allocation(self, allocation: Dict[str, float]) -> str:
        """Format allocation dictionary as string."""
        sorted_alloc = sorted(allocation.items(), key=lambda x: x[1], reverse=True)
        return '\n'.join([f"  - {sector}: {pct:.1f}%" for sector, pct in sorted_alloc])

    def _format_holdings(self, holdings: List[Dict]) -> str:
        """Format holdings list as string."""
        sorted_holdings = sorted(holdings, key=lambda x: x['current_value'], reverse=True)
        lines = []
        for h in sorted_holdings:
            lines.append(
                f"  - {h.get('ticker', h.get('company_name', 'Unknown'))}: {h.get('shares', 0)} shares @ ${h.get('current_price', 0):.2f} = ${h.get('current_value', 0):,.2f}"
            )
        return '\n'.join(lines)

    def get_rebalancing_suggestions(
        self,
        analysis: Dict[str, Any],
        target_allocation: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Generate rebalancing suggestions.

        Args:
            analysis: Portfolio analysis
            target_allocation: Target allocation (uses standard if None)

        Returns:
            Educational rebalancing suggestions
        """
        if target_allocation is None:
            # Use a standard balanced allocation
            target_allocation = {
                'US Stocks': 50,
                'International': 20,
                'Bonds': 25,
                'Other': 5
            }

        current = analysis.get('asset_type_allocation', {})

        prompt = f"""Compare this portfolio's current allocation to a standard balanced allocation and provide educational rebalancing suggestions.

CURRENT ALLOCATION:
{self._format_allocation(current)}

TYPICAL BALANCED ALLOCATION:
{self._format_allocation(target_allocation)}

Please explain:
1. How the current allocation compares to the target
2. What rebalancing means and why it matters
3. General suggestions for moving toward better balance
4. Important considerations (taxes, transaction costs)

Keep it educational and avoid specific financial advice."""

        return self.generate_response(prompt)

    def generate_diversification_recommendations(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific, scored diversification recommendations.

        Args:
            analysis: Portfolio analysis results

        Returns:
            List of recommendation dicts with scores
        """
        recommendations = []
        
        # Get current portfolio characteristics
        sector_allocation = analysis.get('sector_allocation', {})
        total_value = analysis.get('total_value', 0)
        holdings = analysis.get('holdings', [])
        diversification_score = analysis.get('diversification_score', {}).get('score', 0)
        
        # Determine what's missing/underweighted
        has_tech = sector_allocation.get('Technology', 0) > 10
        has_healthcare = sector_allocation.get('Healthcare', 0) > 5
        has_bonds = any(h.get('ticker') in ['BND', 'AGG', 'TLT'] for h in holdings if h.get('ticker'))
        has_international = any(h.get('ticker') in ['VXUS', 'VEA', 'VWO', 'EFA'] for h in holdings if h.get('ticker'))
        has_real_estate = sector_allocation.get('Real Estate', 0) > 3
        
        # Recommendation 1: Bonds for stability
        if not has_bonds:
            recommendations.append({
                'ticker': 'BND',
                'name': 'Vanguard Total Bond Market ETF',
                'category': 'Fixed Income',
                'reason': 'Add bond exposure for stability and income',
                'allocation_suggestion': '20-30% of portfolio',
                'scores': {
                    'risk_score': 2,  # 1-10, lower is safer
                    'return_potential': 5,  # 1-10, higher is better
                    'time_horizon': '1+ years',
                    'annual_yield': '3.5-4.5%',
                    'diversification_benefit': 9,  # 1-10, higher is better
                    'liquidity': 10,  # 1-10, higher is better
                },
                'investment_score': 85,  # Overall score 0-100
                'pros': [
                    'Low volatility compared to stocks',
                    'Regular income through interest payments',
                    'Inverse correlation with stocks (hedges downturns)'
                ],
                'cons': [
                    'Lower long-term returns than stocks',
                    'Interest rate risk (bond prices fall when rates rise)',
                    'Inflation risk'
                ]
            })
        
        # Recommendation 2: International diversification
        if not has_international:
            recommendations.append({
                'ticker': 'VXUS',
                'name': 'Vanguard Total International Stock ETF',
                'category': 'International Equity',
                'reason': 'Diversify beyond US markets',
                'allocation_suggestion': '15-25% of portfolio',
                'scores': {
                    'risk_score': 6,
                    'return_potential': 7,
                    'time_horizon': '5+ years',
                    'annual_yield': '2-3% (dividends)',
                    'diversification_benefit': 10,
                    'liquidity': 10,
                },
                'investment_score': 78,
                'pros': [
                    'Exposure to growing international markets',
                    'Reduces US-specific risk',
                    'Currency diversification'
                ],
                'cons': [
                    'Higher volatility than US markets',
                    'Currency exchange risk',
                    'Political and economic risks in emerging markets'
                ]
            })
        
        # Recommendation 3: Healthcare sector (defensive)
        if not has_healthcare or sector_allocation.get('Healthcare', 0) < 10:
            recommendations.append({
                'ticker': 'VHT',
                'name': 'Vanguard Health Care ETF',
                'category': 'Healthcare Sector',
                'reason': 'Add defensive sector with aging demographics tailwind',
                'allocation_suggestion': '10-15% of portfolio',
                'scores': {
                    'risk_score': 5,
                    'return_potential': 8,
                    'time_horizon': '3+ years',
                    'annual_yield': '1-2% (dividends)',
                    'diversification_benefit': 7,
                    'liquidity': 9,
                },
                'investment_score': 82,
                'pros': [
                    'Defensive sector (people need healthcare in any economy)',
                    'Long-term demographic trends (aging population)',
                    'Innovation in biotech and medical devices'
                ],
                'cons': [
                    'Regulatory risk (government healthcare policies)',
                    'High R&D costs and patent cliffs',
                    'Concentrated in fewer companies than broad market'
                ]
            })
        
        # Recommendation 4: Real Estate
        if not has_real_estate:
            recommendations.append({
                'ticker': 'VNQ',
                'name': 'Vanguard Real Estate ETF',
                'category': 'Real Estate (REITs)',
                'reason': 'Add real estate exposure for income and inflation hedge',
                'allocation_suggestion': '5-10% of portfolio',
                'scores': {
                    'risk_score': 6,
                    'return_potential': 7,
                    'time_horizon': '5+ years',
                    'annual_yield': '3-5% (dividends)',
                    'diversification_benefit': 8,
                    'liquidity': 9,
                },
                'investment_score': 75,
                'pros': [
                    'High dividend yield from REIT distributions',
                    'Inflation hedge (rents increase with inflation)',
                    'Different risk profile than stocks/bonds'
                ],
                'cons': [
                    'Interest rate sensitive (REITs struggle when rates rise)',
                    'Concentrated risk in real estate market',
                    'Tax treatment (dividends taxed as ordinary income)'
                ]
            })
        
        # Recommendation 5: Value stocks if tech-heavy
        if has_tech and sector_allocation.get('Technology', 0) > 25:
            recommendations.append({
                'ticker': 'VTV',
                'name': 'Vanguard Value ETF',
                'category': 'Value Stocks',
                'reason': 'Balance growth-heavy portfolio with value stocks',
                'allocation_suggestion': '15-20% of portfolio',
                'scores': {
                    'risk_score': 5,
                    'return_potential': 7,
                    'time_horizon': '3+ years',
                    'annual_yield': '2-3% (dividends)',
                    'diversification_benefit': 8,
                    'liquidity': 10,
                },
                'investment_score': 80,
                'pros': [
                    'Lower valuations than growth stocks (margin of safety)',
                    'Higher dividend yields',
                    'Tends to perform well during economic recovery'
                ],
                'cons': [
                    'May underperform during strong bull markets',
                    'Often in mature, slower-growing industries',
                    'Value traps (stocks cheap for good reason)'
                ]
            })
        
        # Sort by investment score (highest first)
        recommendations.sort(key=lambda x: x['investment_score'], reverse=True)
        
        # Return top 3-4 recommendations
        return recommendations[:4]

