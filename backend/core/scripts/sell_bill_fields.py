# backend/core/scripts/add_sell_bill_fields.py
"""
Add SELL bill fields to transactions table

"""

import sqlite3
from pathlib import Path

def add_sell_bill_fields():
    """
    Add sell-specific fields to transactions table
    """
    
    db_path = "D:/Trading_system/trading.db"
    print("="*80)
    print("DATABASE MIGRATION: Adding SELL Bill Fields")
    print("="*80)
    print(f"\nUsing database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQL statements to add sell-specific columns
        migrations = [
            # Sell Bill Information
            ("ALTER TABLE transactions ADD COLUMN sell_bill_number VARCHAR(50);", "sell_bill_number"),
            ("ALTER TABLE transactions ADD COLUMN sell_bill_date DATE;", "sell_bill_date"),
            
            # Base Price (for sell transactions)
            ("ALTER TABLE transactions ADD COLUMN base_price FLOAT DEFAULT 0.0;", "base_price"),
            
            # Capital Gain Tax (CGT) - 7.5% annually
            ("ALTER TABLE transactions ADD COLUMN cgt FLOAT DEFAULT 0.0;", "cgt"),
            ("ALTER TABLE transactions ADD COLUMN capital_gain FLOAT DEFAULT 0.0;", "capital_gain"),
            
            # SEBO Details (Sell specific)
            ("ALTER TABLE transactions ADD COLUMN sebo_commission FLOAT DEFAULT 0.0;", "sebo_commission"),
            
            # Effective Rate (for sell)
            ("ALTER TABLE transactions ADD COLUMN eff_rate FLOAT DEFAULT 0.0;", "eff_rate"),
            
            # Payout flag
            ("ALTER TABLE transactions ADD COLUMN payout VARCHAR(10) DEFAULT 'No';", "payout"),
            
            # Capital Office (CO) quantities
            ("ALTER TABLE transactions ADD COLUMN co_qty FLOAT DEFAULT 0.0;", "co_qty"),
            ("ALTER TABLE transactions ADD COLUMN co_amt FLOAT DEFAULT 0.0;", "co_amt"),
            
            # Net Payable Less Closeout
            ("ALTER TABLE transactions ADD COLUMN net_payable_less_closeout FLOAT DEFAULT 0.0;", "net_payable_less_closeout"),
        ]
        
        print("Executing migrations...\n")
        
        for i, (sql, column_name) in enumerate(migrations, 1):
            try:
                cursor.execute(sql)
                print(f"[{i}/{len(migrations)}] ✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print(f"[{i}/{len(migrations)}] ⚠ Column already exists: {column_name}")
                else:
                    print(f"[{i}/{len(migrations)}] ✗ Error: {e}")
                    raise
        
        conn.commit()
        print("\n" + "="*80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*80)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print("\n" + "="*80)
        print(f"❌ MIGRATION FAILED: {e}")
        print("="*80)
        return False
    finally:
        cursor.close()
        conn.close()


def verify_migration():
    """
    Verify that all columns were added successfully
    """
    print("\n" + "="*80)
    print("Verifying migration...")
    print("="*80)
    
    db_path = "D:/Trading_system/trading.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check transactions table columns
        cursor.execute("PRAGMA table_info(transactions);")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_columns = [
            'sell_bill_number', 'sell_bill_date', 'base_price', 'cgt', 
            'capital_gain', 'sebo_commission', 'eff_rate', 'payout',
            'co_qty', 'co_amt', 'net_payable_less_closeout'
        ]
        
        print("\nChecking transactions table:")
        all_present = True
        for col in expected_columns:
            if col in columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} - MISSING!")
                all_present = False
        
        if all_present:
            print("\n✅ All sell bill fields verified successfully!")
            return True
        else:
            print("\n⚠ Some fields are missing!")
            return False
        
    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DATABASE MIGRATION: SELL BILL FIELDS")
    print("="*80)
    print("\nThis will add sell bill fields to your transactions table.")
    print("Fields: sell_bill_number, sell_bill_date, base_price, cgt, capital_gain, etc.")
    print("\nMake sure to backup your database before proceeding!\n")
    
    response = input("Continue with migration? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = add_sell_bill_fields()
        
        if success:
            verify_migration()
            
            print("\n" + "="*80)
            print("✅ MIGRATION COMPLETED!")
            print("="*80)
            print("\nYou can now:")
            print("1. Record sell transactions with bill details")
            print("2. Track CGT (Capital Gain Tax) at 7.5%")
            print("3. Store sell bill numbers and dates")
            print("4. Track CO quantities and amounts")
            print("="*80 + "\n")
        else:
            print("\n❌ Migration had errors.")
    else:
        print("\nMigration cancelled.")
        