# backend/core/utils/cgt_calculator.py
"""
Capital Gain Tax (CGT) Calculator
CGT is 7.5% of profit, calculated annually
"""

from datetime import datetime, timedelta

def calculate_cgt(
    sell_price: float,
    buy_price: float,
    quantity: int,
    buy_date: datetime,
    sell_date: datetime
) -> dict:
    """
    Calculate Capital Gain Tax (CGT) at 7.5%
    
    Args:
        sell_price: Selling price per share
        buy_price: Original buying price per share
        quantity: Number of shares
        buy_date: Date of purchase
        sell_date: Date of sale
    
    Returns:
        dict with capital_gain, cgt, and holding_period
    """
    
    # Calculate capital gain (profit)
    capital_gain = (sell_price - buy_price) * quantity
    
    # CGT is 7.5% of profit (only on gains, not losses)
    cgt = max(0, capital_gain * 0.075)
    
    # Calculate holding period
    holding_days = (sell_date - buy_date).days
    
    return {
        'capital_gain': round(capital_gain, 2),
        'cgt': round(cgt, 2),
        'holding_days': holding_days,
        'cgt_rate': 0.075  # 7.5%
    }


def calculate_sell_bill_totals(
    quantity: int,
    rate: float,
    base_price: float,
    sebn_commission_rate: float = 0.0033,
    nepse_commission_rate: float = 0.00332,
    sebon_fee_rate: float = 0.000997,
    broker_commission_rate: float = 0.0036,
    sebo_commission_rate: float = 0.00144,
    dp_amount: float = 25.0
) -> dict:
    """
    Calculate all sell bill amounts
    
    Returns complete breakdown of sell transaction
    """
    
    # Amount = Quantity × Rate
    amount = quantity * rate
    
    # Commissions
    sebn_comm = amount * sebn_commission_rate
    nepse_comm = amount * nepse_commission_rate
    sebon_fee = amount * sebon_fee_rate
    broker_comm = amount * broker_commission_rate
    sebo_comm = amount * sebo_commission_rate
    
    # Total commission
    total_commission = sebn_comm + nepse_comm + sebon_fee + broker_comm + sebo_comm + dp_amount
    
    # Capital gain and CGT
    capital_gain = (rate - base_price) * quantity
    cgt = max(0, capital_gain * 0.075)  # 7.5% on profit only
    
    # Effective rate
    eff_rate = rate + (total_commission / quantity) if quantity > 0 else rate
    
    # Net payable less closeout
    net_payable = amount - total_commission - cgt
    
    return {
        'amount': round(amount, 2),
        'sebn_commission': round(sebn_comm, 2),
        'nepse_commission': round(nepse_comm, 2),
        'sebon_regulatory_fee': round(sebon_fee, 2),
        'broker_commission': round(broker_comm, 2),
        'sebo_commission': round(sebo_comm, 2),
        'dp_amount': dp_amount,
        'total_commission': round(total_commission, 2),
        'capital_gain': round(capital_gain, 2),
        'cgt': round(cgt, 2),
        'eff_rate': round(eff_rate, 2),
        'net_payable_less_closeout': round(net_payable, 2)
    }