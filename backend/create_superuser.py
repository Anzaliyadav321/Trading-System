

from sqlalchemy.orm import Session
from core.database import engine
from core.auth.models import User
from core.security import hash_password

def create_superuser():
    """Create or update superuser account for PO"""
    
    # Configuration - CHANGE THE PASSWORD!
    EMAIL = "trade8561@gmail.com"
    PASSWORD = "Admin@123"  # ⚠️ CHANGE THIS PASSWORD!
    
    print("\n" + "=" * 60)
    print("       CREATING SUPERUSER (PO) ACCOUNT")
    print("=" * 60)
    
    # Create database session
    db = Session(engine)
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == EMAIL).first()
        
        if existing_user:
            print(f"\n📧 User {EMAIL} already exists in database!")
            print("🔄 Updating to superuser privileges...")
            
            # Update all possible superuser fields
            if hasattr(existing_user, 'is_superuser'):
                existing_user.is_superuser = True
            if hasattr(existing_user, 'is_verified'):
                existing_user.is_verified = True
            if hasattr(existing_user, 'is_active'):
                existing_user.is_active = True
            if hasattr(existing_user, 'role'):
                existing_user.role = 'admin'
            
            db.commit()
            
            print("\n✅ Successfully updated to SUPERUSER!")
            print(f"\n   Email: {EMAIL}")
            print(f"   All available admin fields updated!")
            
        else:
            print(f"\n📝 Creating new superuser account...")
            print(f"   Email: {EMAIL}")
            
            # Create user with ONLY the basic required fields
            new_superuser = User(
                email=EMAIL,
                hashed_password=hash_password(PASSWORD)
            )
            
            db.add(new_superuser)
            db.flush()  # Get the ID without committing
            
            # Now set additional fields if they exist
            if hasattr(new_superuser, 'is_superuser'):
                new_superuser.is_superuser = True
            if hasattr(new_superuser, 'is_verified'):
                new_superuser.is_verified = True
            if hasattr(new_superuser, 'is_active'):
                new_superuser.is_active = True
            if hasattr(new_superuser, 'role'):
                new_superuser.role = 'admin'
            
            db.commit()
            db.refresh(new_superuser)
            
            print("\n✅ SUPERUSER CREATED SUCCESSFULLY!")
            print("\n" + "-" * 60)
            print("   LOGIN CREDENTIALS:")
            print("-" * 60)
            print(f"   Email:    {EMAIL}")
            print(f"   Password: {PASSWORD}")
            print(f"   Role:     SUPERUSER (PO)")
            print("-" * 60)
            print("\n⚠️  IMPORTANT: Change the password after first login!")
        
        print("\n" + "=" * 60)
        print("   NEXT STEPS:")
        print("=" * 60)
        print("   1. Open your frontend (http://localhost:3000)")
        print(f"   2. Login with: {EMAIL}")
        print("   3. You now have full PO/Admin access!")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 Starting superuser creation process...")
    success = create_superuser()
    
    if success:
        print("✅ Process completed successfully!\n")
    else:
        print("❌ Process failed. Check error messages above.\n")