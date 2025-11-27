import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from core.database import engine
from core.auth.models import User

def check_superuser():
    with Session(engine) as db:
        # Find user by email
        user = db.query(User).filter(User.email == "trade8561@gmail.com").first()
        
        if not user:
            print("❌ User not found!")
            return
        
        print("=" * 60)
        print("USER DETAILS")
        print("=" * 60)
        print(f"Email:        {user.email}")
        print(f"ID:           {user.id}")
        print(f"Is Verified:  {getattr(user, 'is_verified', 'N/A')}")
        print(f"Is Active:    {getattr(user, 'is_active', 'N/A')}")
        print(f"Is Superuser: {getattr(user, 'is_superuser', 'N/A')}")
        print(f"Role:         {getattr(user, 'role', 'N/A')}")
        print("=" * 60)
        
        # Check if is_superuser exists
        if not hasattr(user, 'is_superuser'):
            print("\n⚠️  WARNING: User model doesn't have 'is_superuser' field!")
            print("   Check your User model in core/auth/models.py")
        elif not getattr(user, 'is_superuser', False):
            print("\n❌ User is NOT a superuser!")
            print("   Run create_superuser.py again to fix this")
        else:
            print("\n✅ User IS a superuser!")

if __name__ == "__main__":
    check_superuser()