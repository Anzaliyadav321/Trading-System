# backend/core/scripts/create_and_migrate.py
import sqlite3
from pathlib import Path

def create_transactions_table():
    """Create transactions table if it doesn't exist"""
    
    db_path = "D:/Trading_system/trading.db"
    print("="*80)
    print("CREATING TRANSACTIONS TABLE")
    print("="*80)
    print(f"\nUsing database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create transactions table with ALL fields including new bill details
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            transaction_type VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            stop_loss_price REAL,
            notes TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Bill Information
            bill_number VARCHAR(50),
            bill_date DATE,
            
            -- Financial Breakdown
            sub_total REAL DEFAULT 0.0,
            grand_total REAL DEFAULT 0.0,
            share_amount REAL DEFAULT 0.0,
            share_quantity INTEGER DEFAULT 0,
            
            -- Commission Details
            sebn_commission REAL DEFAULT 0.0,
            nepse_commission REAL DEFAULT 0.0,
            sebon_regulatory_fee REAL DEFAULT 0.0,
            broker_commission REAL DEFAULT 0.0,
            name_transfer_amount REAL DEFAULT 0.0,
            dp_amount REAL DEFAULT 0.0,
            total_commission REAL DEFAULT 0.0,
            
            -- Clearance and Settlement
            clearance_date DATE,
            net_receivable_amount REAL DEFAULT 0.0,
            
            -- Broker Details
            broker_name VARCHAR(200),
            broker_number VARCHAR(50),
            
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transactions(symbol);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_bill_number ON transactions(bill_number);")
        
        conn.commit()
        
        print("✓ transactions table created successfully")
        print("✓ Indexes created")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating transactions table: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def create_transaction_items_table():
    """Create transaction_items table"""
    
    db_path = "D:/Trading_system/trading.db"
    print("\n" + "="*80)
    print("CREATING TRANSACTION_ITEMS TABLE")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            company_name VARCHAR(200) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            quantity INTEGER NOT NULL,
            rate REAL NOT NULL,
            amount REAL NOT NULL,
            commission_rate REAL DEFAULT 0.0,
            commission_amount REAL DEFAULT 0.0,
            nt_amount REAL DEFAULT 0.0,
            sebn_commission REAL DEFAULT 0.0,
            eff_rate REAL DEFAULT 0.0,
            total REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_items_transaction_id ON transaction_items(transaction_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_items_symbol ON transaction_items(symbol);")
        
        conn.commit()
        
        print("✓ transaction_items table created successfully")
        print("✓ Indexes created")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating transaction_items table: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def verify_tables():
    """Verify tables were created"""
    
    db_path = "D:/Trading_system/trading.db"
    print("\n" + "="*80)
    print("VERIFYING TABLES")
    print("="*80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check transactions table
        cursor.execute("PRAGMA table_info(transactions);")
        trans_cols = cursor.fetchall()
        
        print(f"\ntransactions table: {len(trans_cols)} columns")
        
        # Check for bill-related columns
        bill_cols = ['bill_number', 'bill_date', 'sub_total', 'grand_total', 
                     'broker_commission', 'total_commission', 'clearance_date']
        
        for col_name in bill_cols:
            exists = any(col[1] == col_name for col in trans_cols)
            print(f"  {'✓' if exists else '✗'} {col_name}")
        
        # Check transaction_items table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transaction_items';")
        items_exists = cursor.fetchone() is not None
        
        print(f"\ntransaction_items table: {'✓ EXISTS' if items_exists else '✗ MISSING'}")
        
        if items_exists:
            cursor.execute("PRAGMA table_info(transaction_items);")
            items_cols = cursor.fetchall()
            print(f"  Columns: {len(items_cols)}")
        
        print("\n" + "="*80)
        print("✅ ALL TABLES CREATED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"✗ Verification error: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DATABASE SETUP: TRANSACTIONS WITH BILL DETAILS")
    print("="*80)
    print("\nThis will create:")
    print("1. transactions table (with all bill fields)")
    print("2. transaction_items table (for multiple items per bill)")
    print("\nMake sure to backup your database first!\n")
    
    response = input("Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = True
        
        if not create_transactions_table():
            success = False
        
        if success and not create_transaction_items_table():
            success = False
        
        if success:
            verify_tables()
            
            print("\n✅ Setup complete! You can now:")
            print("1. Restart your backend server")
            print("2. Create transactions with bill details")
            print("3. Use the API endpoints for transactions")
        else:
            print("\n❌ Setup had errors")
    else:
        print("\nSetup cancelled.")