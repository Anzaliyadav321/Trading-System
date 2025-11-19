# backend/core/risk_management/portfolio_management.py

"""
Portfolio Management System
Handles capital tracking, validation, and position management
"""

from typing import Tuple, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from backend.core.auth.models import UserPortfolio, Position, DailyEntry, PositionStatus


class PortfolioManager:
    """
    Manages user portfolio - capital, cash, and investment tracking
    """
    
    DEFAULT_CAPITAL = 1000000.0  # ₹10 lakh default
    ALLOCATION_DAYS = 4  # Days 1-4 for buying
    
    # ============================================
    # PORTFOLIO INITIALIZATION
    # ============================================
    
    @staticmethod
    def initialize_portfolio(user_email: str, total_capital: float, db: Session) -> UserPortfolio:
        """
        Initialize user's portfolio with starting capital
        
        Args:
            user_email: User's email
            total_capital: Starting capital (default: ₹10 lakh)
            db: Database session
        
        Returns:
            UserPortfolio object
        """
        # Check if already exists
        existing = db.query(UserPortfolio).filter(
            UserPortfolio.user_email == user_email
        ).first()
        
        if existing:
            raise ValueError(f"Portfolio already exists for {user_email}")
        
        # Create portfolio
        portfolio = UserPortfolio(
            user_email=user_email,
            total_capital=total_capital,
            available_cash=total_capital,
            invested_amount=0.0
        )
        
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        
        return portfolio
    
    @staticmethod
    def get_portfolio(user_email: str, db: Session) -> Optional[UserPortfolio]:
        """Get user's portfolio"""
        return db.query(UserPortfolio).filter(
            UserPortfolio.user_email == user_email
        ).first()
    
    @staticmethod
    def add_capital(user_email: str, amount: float, db: Session) -> UserPortfolio:
        """
        Add capital to user's portfolio (for future growth)
        
        Args:
            user_email: User's email
            amount: Amount to add
            db: Database session
        
        Returns:
            Updated portfolio
        """
        portfolio = PortfolioManager.get_portfolio(user_email, db)
        
        if not portfolio:
            raise ValueError(f"Portfolio not found for {user_email}")
        
        portfolio.total_capital += amount
        portfolio.available_cash += amount
        portfolio.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(portfolio)
        
        return portfolio
    
    # ============================================
    # CAPITAL VALIDATION
    # ============================================
    
    @staticmethod
    def validate_sufficient_cash(
        user_email: str, 
        required_amount: float, 
        db: Session
    ) -> Tuple[bool, str]:
        """
        Validate if user has sufficient cash
        
        Returns:
            (is_valid, message)
        """
        portfolio = PortfolioManager.get_portfolio(user_email, db)
        
        if not portfolio:
            return False, "Portfolio not initialized"
        
        if portfolio.available_cash < required_amount:
            return False, f"Insufficient cash. Available: ₹{portfolio.available_cash:,.2f}, Required: ₹{required_amount:,.2f}"
        
        return True, "Sufficient cash available"
    
    @staticmethod
    def get_allocation_amount(total_capital: float, day_number: int) -> float:
        """
        Get allocation amount for a specific day (25% per day for Days 1-4)
        
        Args:
            total_capital: Total portfolio capital
            day_number: Day 1, 2, 3, or 4
        
        Returns:
            Amount to allocate
        """
        if day_number < 1 or day_number > PortfolioManager.ALLOCATION_DAYS:
            return 0.0
        
        return total_capital / PortfolioManager.ALLOCATION_DAYS
    
    # ============================================
    # CASH MANAGEMENT
    # ============================================
    
    @staticmethod
    def deduct_cash(user_email: str, amount: float, db: Session) -> UserPortfolio:
        """
        Deduct cash from portfolio (when buying)
        
        Args:
            user_email: User's email
            amount: Amount to deduct
            db: Database session
        
        Returns:
            Updated portfolio
        """
        portfolio = PortfolioManager.get_portfolio(user_email, db)
        
        if not portfolio:
            raise ValueError(f"Portfolio not found for {user_email}")
        
        if portfolio.available_cash < amount:
            raise ValueError(f"Insufficient cash. Available: ₹{portfolio.available_cash:,.2f}")
        
        portfolio.available_cash -= amount
        portfolio.invested_amount += amount
        portfolio.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(portfolio)
        
        return portfolio
    
    @staticmethod
    def add_cash(user_email: str, amount: float, db: Session) -> UserPortfolio:
        """
        Add cash to portfolio (when selling)
        
        Args:
            user_email: User's email
            amount: Amount to add
            db: Database session
        
        Returns:
            Updated portfolio
        """
        portfolio = PortfolioManager.get_portfolio(user_email, db)
        
        if not portfolio:
            raise ValueError(f"Portfolio not found for {user_email}")
        
        portfolio.available_cash += amount
        portfolio.invested_amount -= min(amount, portfolio.invested_amount)
        portfolio.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(portfolio)
        
        return portfolio
    
    # ============================================
    # PORTFOLIO SUMMARY
    # ============================================
    
    @staticmethod
    def get_portfolio_summary(user_email: str, db: Session) -> dict:
        """
        Get complete portfolio summary
        
        Returns:
            Dictionary with portfolio stats
        """
        portfolio = PortfolioManager.get_portfolio(user_email, db)
        
        if not portfolio:
            return {
                "initialized": False,
                "message": "Portfolio not initialized"
            }
        
        # Get active positions
        active_positions = db.query(Position).filter(
            Position.user_email == user_email,
            Position.status == PositionStatus.ACTIVE
        ).all()
        
        # Calculate current values
        total_current_value = sum(
            pos.current_price * pos.total_quantity 
            for pos in active_positions
        )
        
        total_unrealized_pl = sum(
            (pos.current_price - pos.avg_buy_price) * pos.total_quantity
            for pos in active_positions
        )
        
        # Get closed positions for realized P&L
        closed_positions = db.query(Position).filter(
            Position.user_email == user_email,
            Position.status == PositionStatus.CLOSED
        ).all()
        
        total_realized_pl = sum(pos.profit_loss for pos in closed_positions)
        
        return {
            "initialized": True,
            "total_capital": portfolio.total_capital,
            "available_cash": portfolio.available_cash,
            "invested_amount": portfolio.invested_amount,
            "current_positions_value": total_current_value,
            "unrealized_profit_loss": total_unrealized_pl,
            "realized_profit_loss": total_realized_pl,
            "total_profit_loss": total_realized_pl + total_unrealized_pl,
            "active_positions_count": len(active_positions),
            "closed_positions_count": len(closed_positions),
            "portfolio_value": portfolio.available_cash + total_current_value,
            "updated_at": portfolio.updated_at.isoformat()
        }
    
    # ============================================
    # UTILITY FUNCTIONS
    # ============================================
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format amount as Indian currency"""
        return f"₹{amount:,.2f}"
    
    @staticmethod
    def format_percent(percent: float) -> str:
        """Format percentage with sign"""
        sign = "+" if percent >= 0 else ""
        return f"{sign}{percent:.2f}%"


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    """
    Example usage of PortfolioManager
    """
    print("=" * 80)
    print("PORTFOLIO MANAGER - EXAMPLE USAGE")
    print("=" * 80)
    
    # Example: Get allocation amount
    print("\n Allocation Calculation:")
    total_capital = 1000000  # ₹10 lakh
    for day in range(1, 5):
        amount = PortfolioManager.get_allocation_amount(total_capital, day)
        print(f"Day {day}: {PortfolioManager.format_currency(amount)}")
    
    # Example: Validate sufficient cash
    print("\nCash Validation:")
    print(f"Total Capital: {PortfolioManager.format_currency(total_capital)}")
    print(f"Required: {PortfolioManager.format_currency(250000)}")
    print(f"Available: {PortfolioManager.format_currency(1000000)}")
    print(f"Valid? {1000000 >= 250000}")
    
    print("\n" + "=" * 80)