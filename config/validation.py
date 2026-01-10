import os
import sys

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'GOOGLE_PROJECT_ID',
        'GOOGLE_PRIVATE_KEY_ID',
        'GOOGLE_PRIVATE_KEY',
        'GOOGLE_CLIENT_EMAIL',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_SHEET_ID',
        'ADMIN_PHONE'
    ]
    
    missing_vars = []
    empty_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value is None:
            missing_vars.append(var)
        elif not value.strip():
            empty_vars.append(var)
    
    if missing_vars or empty_vars:
        print("❌ Environment validation failed!")
        if missing_vars:
            print(f"Missing environment variables: {', '.join(missing_vars)}")
        if empty_vars:
            print(f"Empty environment variables: {', '.join(empty_vars)}")
        print("\n📝 Please check your .env file or Railway environment variables")
        print("📖 See README.md for setup instructions")
        return False
    
    # Validate admin phone format
    admin_phone = os.environ.get('ADMIN_PHONE', '')
    if not admin_phone.startswith('+'):
        print("❌ ADMIN_PHONE must start with country code (e.g. +1234567890)")
        return False
    
    print("✅ All environment variables validated successfully!")
    return True

if __name__ == "__main__":
    if not validate_environment():
        sys.exit(1)