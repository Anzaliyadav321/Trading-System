# backend/core/risk_management/stop_loss_management.py

"""
Stop Loss Management System
Implements the complete TradingSystem logic for database-backed positions

Rules:
- Day 1: 5% SL from buying price
- Days 2-4: 5% Trailing SL from average price
- Day 5+: Progressive Trailing SL based on profit levels
  • Until 20% profit: 5% Trailing SL from max closing price
  • 20%+ profit: 7% Trailing SL from max closing price
  • 30%+ profit: 8.5% Trailing SL from max closing price
  • 40%+ profit: 18% Trailing SL from max closing price
- Mandatory exit after 90 days
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from sqlalchemy.orm import Session

# These will be your database models (uncomment after creating models.py)
# from backend.core.auth.models import Position, DailyEntry, UserPortfolio, PositionStatus


class StopLossManager:
    """
    Core stop loss calculation and management system
    Implements all SL rules from TradingSystem
    """
    
    # Configuration constants
    INITIAL_SL_PERCENT = 5.0  # Day 1 SL percentage
    TRAILING_SL_PERCENT = 5.0  # Days 2-4 trailing SL percentage
    MAX_HOLDING_DAYS = 90  # 3 months mandatory exit
    
    # Profit level thresholds
    PROFIT_LEVEL_20 = 0.20  # 20% profit
    PROFIT_LEVEL_30 = 0.30  # 30% profit
    PROFIT_LEVEL_40 = 0.40  # 40% profit
    
    # SL percentages for each profit level (Day 5+)
    SL_PERCENTAGES = {
        'default': 0.05,   # 5% until 20% profit
        'level_20': 0.07,  # 7% trailing SL
        'level_30': 0.085, # 8.5% trailing SL
        'level_40': 0.18   # 18% trailing SL
    }
    
    # SL level hierarchy (cannot downgrade)
    LEVEL_HIERARCHY = ["default", "level_20", "level_30", "level_40"]
    
    # ============================================
    # DAY 1 CALCULATIONS
    # ============================================
    
    @staticmethod
    def calculate_day1_sl(entry_price: float, sl_percent: float = None) -> float:
        """
        Calculate Day 1 stop loss from buying price
        
        Args:
            entry_price: The price at which stock was bought
            sl_percent: Stop loss percentage (default: 5%)
        
        Returns:
            Stop loss price
        
        Example:
            Entry: ₹200
            SL: ₹200 * (1 - 0.05) = ₹190
        """
        if sl_percent is None:
            sl_percent = StopLossManager.INITIAL_SL_PERCENT
        
        return entry_price * (1 - sl_percent / 100)
    
    @staticmethod
    def check_day1_sl_hit(entry_price: float, current_price: float) -> Tuple[bool, float, str]:
        """
        Check if Day 1 stop loss is hit
        
        Returns:
            (is_hit, sl_price, reason)
        """
        sl_price = StopLossManager.calculate_day1_sl(entry_price)
        is_hit = current_price <= sl_price
        
        reason = ""
        if is_hit:
            reason = f"Day 1 SL hit: Current price ₹{current_price} ≤ SL ₹{sl_price:.2f}"
        
        return is_hit, sl_price, reason
    
    # ============================================
    # DAYS 2-4 CALCULATIONS
    # ============================================
    
    @staticmethod
    def calculate_weighted_average_price(daily_entries: List[Tuple[float, float]]) -> float:
        """
        Calculate weighted average price from multiple entries
        
        Args:
            daily_entries: List of (price, amount) tuples
        
        Returns:
            Weighted average price
        
        Example:
            Day 1: ₹200 with ₹25,000 → 125 shares
            Day 2: ₹195 with ₹25,000 → 128.2 shares
            Avg: (200*125 + 195*128.2) / (125 + 128.2) = ₹197.48
        """
        if not daily_entries:
            return 0
        
        total_value = sum(price * amount for price, amount in daily_entries)
        total_amount = sum(amount for _, amount in daily_entries)
        
        return total_value / total_amount if total_amount > 0 else 0
    
    @staticmethod
    def calculate_trailing_sl_from_avg(avg_price: float, sl_percent: float = None) -> float:
        """
        Calculate 5% trailing SL from average price (Days 2-4)
        
        Args:
            avg_price: Weighted average buy price
            sl_percent: Trailing SL percentage (default: 5%)
        
        Returns:
            Trailing stop loss price
        
        Example:
            Avg Price: ₹197.48
            Trailing SL: ₹197.48 * (1 - 0.05) = ₹187.61
        """
        if sl_percent is None:
            sl_percent = StopLossManager.TRAILING_SL_PERCENT
        
        return avg_price * (1 - sl_percent / 100)
    
    @staticmethod
    def check_trailing_sl_hit(avg_price: float, current_price: float) -> Tuple[bool, float, str]:
        """
        Check if Days 2-4 trailing SL is hit
        
        Returns:
            (is_hit, sl_price, reason)
        """
        sl_price = StopLossManager.calculate_trailing_sl_from_avg(avg_price)
        is_hit = current_price <= sl_price
        
        reason = ""
        if is_hit:
            reason = f"Days 2-4 Trailing SL hit: Current price ₹{current_price} ≤ SL ₹{sl_price:.2f}"
        
        return is_hit, sl_price, reason
    
    # ============================================
    # DAY 5+ PROGRESSIVE TRAILING SL CALCULATIONS
    # ============================================
    
    @staticmethod
    def get_applicable_sl_level(current_profit_percent: float) -> Tuple[str, float, str]:
        """
        Determine applicable SL level based on current profit percentage
        
        Args:
            current_profit_percent: Current profit as decimal (0.25 = 25%)
        
        Returns:
            (level_name, sl_percentage, description)
        
        Example:
            Profit = 25% → ('level_20', 0.07, '7% TRAILING SL')
        """
        if current_profit_percent >= StopLossManager.PROFIT_LEVEL_40:
            return 'level_40', StopLossManager.SL_PERCENTAGES['level_40'], "18% TRAILING SL"
        elif current_profit_percent >= StopLossManager.PROFIT_LEVEL_30:
            return 'level_30', StopLossManager.SL_PERCENTAGES['level_30'], "8.5% TRAILING SL"
        elif current_profit_percent >= StopLossManager.PROFIT_LEVEL_20:
            return 'level_20', StopLossManager.SL_PERCENTAGES['level_20'], "7% TRAILING SL"
        else:
            return 'default', StopLossManager.SL_PERCENTAGES['default'], "5% TRAILING SL"
    
    @staticmethod
    def determine_highest_sl_level(current_level: str, previous_highest: str) -> str:
        """
        Determine highest SL level achieved (prevents downgrade)
        
        Args:
            current_level: Current profit-based SL level
            previous_highest: Previously achieved highest level
        
        Returns:
            Highest level (current or previous)
        
        Example:
            Previously achieved: level_30
            Current profit drops to level_20
            Result: Still use level_30 (no downgrade)
        """
        current_index = StopLossManager.LEVEL_HIERARCHY.index(current_level)
        previous_index = StopLossManager.LEVEL_HIERARCHY.index(previous_highest)
        
        if current_index > previous_index:
            return current_level
        else:
            return previous_highest
    
    @staticmethod
    def calculate_day5_plus_sl(
        max_closing_price: float,
        current_profit_percent: float,
        highest_level_achieved: str = "default"
    ) -> Tuple[float, str, str]:
        """
        Calculate Day 5+ progressive trailing SL from max closing price
        
        Args:
            max_closing_price: Highest closing price seen so far
            current_profit_percent: Current profit as decimal
            highest_level_achieved: Highest SL level previously achieved
        
        Returns:
            (sl_price, sl_level, description)
        
        Example:
            Max closing: ₹250
            Current profit: 35%
            Highest achieved: level_20
            Current level: level_30 (35% profit)
            Result: Use level_30 (upgrade allowed)
            SL = ₹250 * (1 - 0.085) = ₹228.75
        """
        # Get current applicable level
        current_level, current_sl_percent, current_desc = StopLossManager.get_applicable_sl_level(
            current_profit_percent
        )
        
        # Determine highest level (no downgrade)
        final_level = StopLossManager.determine_highest_sl_level(
            current_level,
            highest_level_achieved
        )
        
        # Calculate SL from highest level achieved
        final_sl_percent = StopLossManager.SL_PERCENTAGES[final_level]
        sl_price = max_closing_price * (1 - final_sl_percent)
        
        # Create description
        level_descriptions = {
            'level_40': "18% TRAILING SL (40%+ profit level)",
            'level_30': "8.5% TRAILING SL (30%+ profit level)",
            'level_20': "7% TRAILING SL (20%+ profit level)",
            'default': "5% TRAILING SL (until 20% profit)"
        }
        
        description = level_descriptions.get(final_level, "Unknown SL level")
        
        return sl_price, final_level, description
    
    @staticmethod
    def check_day5_plus_sl_hit(
        current_price: float,
        sl_price: float,
        sl_description: str
    ) -> Tuple[bool, str]:
        """
        Check if Day 5+ progressive trailing SL is hit
        
        Returns:
            (is_hit, reason)
        """
        is_hit = current_price <= sl_price
        
        reason = ""
        if is_hit:
            reason = f"{sl_description} hit: Current price ₹{current_price} ≤ SL ₹{sl_price:.2f}"
        
        return is_hit, reason
    
    # ============================================
    # POSITION ANALYSIS & DECISION MAKING
    # ============================================
    
    @staticmethod
    def calculate_position_profit(
        avg_buy_price: float,
        current_price: float,
        quantity: float
    ) -> Tuple[float, float, float]:
        """
        Calculate position profit/loss
        
        Returns:
            (current_value, pnl_amount, pnl_percent)
        
        Example:
            Avg buy: ₹197.48
            Current: ₹250
            Quantity: 250 shares
            
            Current value: ₹250 * 250 = ₹62,500
            Investment: ₹197.48 * 250 = ₹49,370
            P&L: ₹62,500 - ₹49,370 = +₹13,130 (26.6%)
        """
        if avg_buy_price == 0 or quantity == 0:
            return 0, 0, 0
        
        investment = avg_buy_price * quantity
        current_value = current_price * quantity
        pnl_amount = current_value - investment
        pnl_percent = (pnl_amount / investment) * 100
        
        return current_value, pnl_amount, pnl_percent
    
    @staticmethod
    def make_trading_decision(
        days_held: int,
        entry_price: float,
        avg_buy_price: float,
        current_price: float,
        max_closing_price: float,
        sl_level: str,
        quantity: float,
        daily_entries: List[Tuple[float, float]] = None
    ) -> Dict:
        """
        Make complete trading decision based on position state
        
        Args:
            days_held: Number of days position has been held
            entry_price: Initial entry price (Day 1)
            avg_buy_price: Weighted average buy price
            current_price: Current market price
            max_closing_price: Highest closing price seen
            sl_level: Current SL level achieved
            quantity: Total quantity held
            daily_entries: List of (price, amount) for Days 1-4
        
        Returns:
            Dictionary with decision, SL price, reason, profit info
        
        Example return:
        {
            'decision': 'HOLD',  # or 'SELL'
            'sl_price': 228.75,
            'sl_level': 'level_30',
            'sl_description': '8.5% TRAILING SL (30%+ profit level)',
            'is_sl_hit': False,
            'exit_reason': '',
            'current_value': 62500,
            'pnl_amount': 13130,
            'pnl_percent': 26.6,
            'days_remaining': 85,
            'alerts': []
        }
        """
        result = {
            'decision': 'HOLD',
            'sl_price': 0,
            'sl_level': sl_level,
            'sl_description': '',
            'is_sl_hit': False,
            'exit_reason': '',
            'current_value': 0,
            'pnl_amount': 0,
            'pnl_percent': 0,
            'days_remaining': StopLossManager.MAX_HOLDING_DAYS - days_held,
            'alerts': []
        }
        
        # Calculate current profit
        current_value, pnl_amount, pnl_percent = StopLossManager.calculate_position_profit(
            avg_buy_price, current_price, quantity
        )
        result['current_value'] = current_value
        result['pnl_amount'] = pnl_amount
        result['pnl_percent'] = pnl_percent
        
        # Check mandatory 90-day exit FIRST
        if days_held >= StopLossManager.MAX_HOLDING_DAYS:
            result['decision'] = 'SELL'
            result['exit_reason'] = f"MANDATORY EXIT after {StopLossManager.MAX_HOLDING_DAYS} days (3 months)"
            result['is_sl_hit'] = False
            return result
        
        # DAY 1: Check 5% SL from buying price
        if days_held == 1:
            is_hit, sl_price, reason = StopLossManager.check_day1_sl_hit(entry_price, current_price)
            result['sl_price'] = sl_price
            result['sl_description'] = "5% SL from buying price"
            
            if is_hit:
                result['decision'] = 'SELL'
                result['is_sl_hit'] = True
                result['exit_reason'] = reason
        
        # DAYS 2-4: Check 5% Trailing SL from average price
        elif days_held >= 2 and days_held <= 4:
            is_hit, sl_price, reason = StopLossManager.check_trailing_sl_hit(avg_buy_price, current_price)
            result['sl_price'] = sl_price
            result['sl_description'] = "5% Trailing SL from average price"
            
            if is_hit:
                result['decision'] = 'SELL'
                result['is_sl_hit'] = True
                result['exit_reason'] = reason
        
        # DAY 5+: Check progressive trailing SL
        elif days_held >= 5:
            current_profit_percent = (current_price - avg_buy_price) / avg_buy_price
            
            # Calculate Day 5+ SL
            sl_price, new_sl_level, sl_desc = StopLossManager.calculate_day5_plus_sl(
                max_closing_price,
                current_profit_percent,
                sl_level
            )
            
            result['sl_price'] = sl_price
            result['sl_level'] = new_sl_level
            result['sl_description'] = sl_desc
            
            # Check if SL hit
            is_hit, reason = StopLossManager.check_day5_plus_sl_hit(
                current_price, sl_price, sl_desc
            )
            
            if is_hit:
                result['decision'] = 'SELL'
                result['is_sl_hit'] = True
                result['exit_reason'] = reason
            
            # Add alerts
            # Alert 1: Price below average buy price
            if current_price < avg_buy_price:
                drop_amount = avg_buy_price - current_price
                drop_percent = (drop_amount / avg_buy_price) * 100
                result['alerts'].append(
                    f"PRICE BELOW AVG: Current ₹{current_price} is ₹{drop_amount:.2f} "
                    f"({drop_percent:.1f}%) below average buy price ₹{avg_buy_price:.2f}"
                )
            
            # Alert 2: 40% profit level achievement
            if current_profit_percent >= StopLossManager.PROFIT_LEVEL_40:
                if sl_level != 'level_40':  # First time achieving 40%
                    result['alerts'].append(
                        "🎉 40%+ profit level reached! Now using 18% trailing SL"
                    )
        
        return result
    
    # ============================================
    # UTILITY FUNCTIONS
    # ============================================
    
    @staticmethod
    def should_stop_buying(days_held: int, current_price: float, avg_buy_price: float) -> Tuple[bool, str]:
        """
        Determine if buying should stop (Days 2-4 SL hit during allocation)
        
        Returns:
            (should_stop, reason)
        """
        if days_held >= 2 and days_held <= 4:
            is_hit, sl_price, reason = StopLossManager.check_trailing_sl_hit(avg_buy_price, current_price)
            if is_hit:
                return True, f"Stop buying: Trailing SL hit during allocation. {reason}"
        
        return False, ""
    
    @staticmethod
    def get_allocation_amount(total_capital: float, day_number: int) -> float:
        """
        Get allocation amount for a specific day (Days 1-4)
        
        Args:
            total_capital: Total capital available
            day_number: Day 1, 2, 3, or 4
        
        Returns:
            Amount to allocate (25% of total capital)
        
        Example:
            Total: ₹1,00,000
            Day 1: ₹25,000
            Day 2: ₹25,000
            Day 3: ₹25,000
            Day 4: ₹25,000
        """
        if day_number < 1 or day_number > 4:
            return 0
        
        return total_capital / 4  # 25% each day
    
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
    # DATABASE INTEGRATION METHODS
    # ============================================
    
    @staticmethod
    def update_position_from_db(position, current_price: float, db: Session) -> Dict:
        """
        Update position using database model
        
        Args:
            position: Position model from database
            current_price: Current market price
            db: Database session
        
        Returns:
            Trading decision dictionary
        
        Note:
            Uncomment imports at top of file before using this method:
            from backend.core.auth.models import Position, DailyEntry, UserPortfolio, PositionStatus
        """
        # Get daily entries from database
        daily_entries = [(entry.entry_price, entry.amount_invested) 
                         for entry in position.daily_entries]
        
        # Make trading decision
        decision = StopLossManager.make_trading_decision(
            days_held=position.days_held,
            entry_price=position.entry_price,
            avg_buy_price=position.avg_buy_price,
            current_price=current_price,
            max_closing_price=position.max_closing_price,
            sl_level=position.highest_sl_level_achieved,
            quantity=position.total_quantity,
            daily_entries=daily_entries
        )
        
        # Update database model
        if decision['decision'] == 'SELL':
            # Note: Uncomment this line after importing PositionStatus
            # position.status = PositionStatus.CLOSED
            position.exit_price = current_price
            position.exit_reason = decision['exit_reason']
            position.exit_date = datetime.utcnow()
            position.profit_loss = decision['pnl_amount']
        
        # Update SL tracking
        position.sl_price = decision['sl_price']
        position.highest_sl_level_achieved = decision['sl_level']
        position.current_price = current_price
        
        # Update max closing price
        if current_price > position.max_closing_price:
            position.max_closing_price = current_price
        
        # Check if 40% profit level achieved
        current_profit_percent = (current_price - position.avg_buy_price) / position.avg_buy_price
        if current_profit_percent >= StopLossManager.PROFIT_LEVEL_40:
            position.profit_40_achieved = True
        
        position.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(position)
        
        return decision
    
    @staticmethod
    def check_all_positions(user_email: str, current_prices: Dict[str, float], db: Session) -> List[Dict]:
        """
        Check all active positions for a user and update them
        
        Args:
            user_email: User's email
            current_prices: Dictionary of {symbol: current_price}
            db: Database session
        
        Returns:
            List of trading decisions for all positions
        
        Note:
            Uncomment imports at top of file before using this method:
            from backend.core.auth.models import Position, PositionStatus
        """
        # Note: Uncomment after importing Position and PositionStatus
        # positions = db.query(Position).filter(
        #     Position.user_email == user_email,
        #     Position.status == PositionStatus.ACTIVE
        # ).all()
        
        # decisions = []
        # for position in positions:
        #     if position.symbol in current_prices:
        #         current_price = current_prices[position.symbol]
        #         decision = StopLossManager.update_position_from_db(
        #             position, current_price, db
        #         )
        #         decisions.append({
        #             'symbol': position.symbol,
        #             'decision': decision
        #         })
        
        # return decisions
        
        # Placeholder return (remove after uncommenting above)
        return []


# ============================================
# EXAMPLE USAGE & TESTING
# ============================================

if __name__ == "__main__":
    """
    Example usage and testing of StopLossManager
    """
    
    print("=" * 80)
    print("STOP LOSS MANAGER - EXAMPLE USAGE")
    print("=" * 80)
    
    # Example 1: Day 1 SL Calculation
    print("\n Example 1: Day 1 SL Calculation")
    entry_price = 200
    sl_price = StopLossManager.calculate_day1_sl(entry_price)
    print(f"Entry Price: ₹{entry_price}")
    print(f"Day 1 SL (5%): ₹{sl_price:.2f}")
    
    current_price = 188
    is_hit, sl, reason = StopLossManager.check_day1_sl_hit(entry_price, current_price)
    print(f"Current Price: ₹{current_price}")
    print(f"SL Hit? {is_hit} - {reason if is_hit else 'Safe'}")
    
    # Example 2: Days 2-4 Trailing SL
    print("\n Example 2: Days 2-4 Trailing SL")
    daily_entries = [(200, 25000), (195, 25000)]  # Day 1 & 2 entries
    avg_price = StopLossManager.calculate_weighted_average_price(daily_entries)
    trailing_sl = StopLossManager.calculate_trailing_sl_from_avg(avg_price)
    print(f"Day 1: ₹200 with ₹25,000")
    print(f"Day 2: ₹195 with ₹25,000")
    print(f"Weighted Avg Price: ₹{avg_price:.2f}")
    print(f"Trailing SL (5%): ₹{trailing_sl:.2f}")
    
    # Example 3: Day 5+ Progressive SL
    print("\n Example 3: Day 5+ Progressive Trailing SL")
    max_closing = 250
    avg_buy = 197.48
    current = 245
    profit_pct = (current - avg_buy) / avg_buy
    
    sl_price, sl_level, sl_desc = StopLossManager.calculate_day5_plus_sl(
        max_closing, profit_pct, "default"
    )
    
    print(f"Max Closing Price: ₹{max_closing}")
    print(f"Average Buy Price: ₹{avg_buy:.2f}")
    print(f"Current Price: ₹{current}")
    print(f"Current Profit: {profit_pct*100:.1f}%")
    print(f"SL Level: {sl_level}")
    print(f"SL Price: ₹{sl_price:.2f}")
    print(f"Description: {sl_desc}")
    
    # Example 4: Complete Trading Decision
    print("\n Example 4: Complete Trading Decision")
    decision = StopLossManager.make_trading_decision(
        days_held=25,
        entry_price=200,
        avg_buy_price=197.48,
        current_price=245,
        max_closing_price=250,
        sl_level="level_20",
        quantity=250,
        daily_entries=[(200, 25000), (195, 25000), (197, 25000), (198, 25000)]
    )
    
    print(f"Decision: {decision['decision']}")
    print(f"SL Price: ₹{decision['sl_price']:.2f}")
    print(f"SL Level: {decision['sl_level']}")
    print(f"SL Description: {decision['sl_description']}")
    print(f"Current Value: ₹{decision['current_value']:,.2f}")
    print(f"P&L: ₹{decision['pnl_amount']:,.2f} ({decision['pnl_percent']:.2f}%)")
    print(f"Days Remaining: {decision['days_remaining']}")
    
    if decision['alerts']:
        print("Alerts:")
        for alert in decision['alerts']:
            print(f"  {alert}")
    
    print("\n" + "=" * 80)
    print("NOTE: Database integration methods are included but commented.")
    print("Uncomment imports and methods after creating database models.")
    print("=" * 80)