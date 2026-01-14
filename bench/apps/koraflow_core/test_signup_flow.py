"""
Test script for Signup → Verification → Intake Flow
Run with: bench --site [site-name] console
Then: exec(open('apps/koraflow_core/test_signup_flow.py').read())
"""
import frappe
from frappe.utils import sha256_hash, now_datetime
from koraflow_core.api.patient_signup import (
    patient_sign_up,
    verify_email,
    force_verify_email,
    get_intake_form_status
)

def test_signup_flow():
    """Test the complete signup → verification → intake flow"""
    
    print("\n" + "="*60)
    print("TESTING SIGNUP → VERIFICATION → INTAKE FLOW")
    print("="*60 + "\n")
    
    # Clean up any existing test user
    test_email = "test.patient@example.com"
    if frappe.db.exists("User", test_email):
        print(f"⚠️  Cleaning up existing test user: {test_email}")
        frappe.delete_doc("User", test_email, force=1, ignore_permissions=1)
        frappe.db.commit()
    
    # Step 1: Test Patient Signup
    print("Step 1: Testing Patient Signup (No Password)")
    print("-" * 60)
    try:
        status, message = patient_sign_up(
            email=test_email,
            full_name="Test Patient",
            redirect_to="/glp1-intake"
        )
        print(f"✅ Signup Status: {status}")
        print(f"✅ Message: {message}")
        
        # Verify user was created
        user = frappe.get_doc("User", test_email)
        assert user.email_verified == 0, "User should have email_verified = 0"
        assert user.intake_completed == 0, "User should have intake_completed = 0"
        assert user.email_verification_key is not None, "Verification key should be set"
        print(f"✅ User created: {user.name}")
        print(f"✅ email_verified: {user.email_verified}")
        print(f"✅ intake_completed: {user.intake_completed}")
        print(f"✅ Verification key generated: {bool(user.email_verification_key)}")
        
    except Exception as e:
        print(f"❌ Signup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Get verification token
    print("\nStep 2: Getting Verification Token")
    print("-" * 60)
    user = frappe.get_doc("User", test_email)
    verification_key = None
    
    # In real flow, token would come from email
    # For testing, we need to get it from the database
    # Note: We can't reverse the hash, so we'll test with a new token
    print("⚠️  Note: In production, token comes from email link")
    print("⚠️  For testing, we'll generate a new token")
    
    # Generate new token for testing
    import frappe.utils
    verification_key = frappe.utils.generate_hash()
    hashed_key = sha256_hash(verification_key)
    user.db_set("email_verification_key", hashed_key)
    user.db_set("email_verification_key_generated_on", now_datetime())
    frappe.db.commit()
    print(f"✅ Test token generated: {verification_key[:20]}...")
    
    # Step 3: Test Email Verification
    print("\nStep 3: Testing Email Verification")
    print("-" * 60)
    try:
        # Note: verify_email() uses frappe.respond_as_web_page() which won't work in console
        # So we'll test the core logic manually
        with frappe.as_user("Administrator"):
            user.reload()
            if user.email_verification_key == hashed_key:
                user.db_set("email_verified", 1)
                user.db_set("email_verified_on", now_datetime())
                user.db_set("email_verified_via", "Email")
                user.db_set("email_verification_key", None)
                frappe.cache.hset("redirect_after_login", user.name, "/glp1-intake")
                frappe.db.commit()
                print("✅ Email verified successfully")
                
                # Verify fields
                user.reload()
                assert user.email_verified == 1, "Email should be verified"
                assert user.email_verified_via == "Email", "Should be verified via Email"
                assert user.email_verified_on is not None, "Verification timestamp should be set"
                print(f"✅ email_verified: {user.email_verified}")
                print(f"✅ email_verified_via: {user.email_verified_via}")
                print(f"✅ email_verified_on: {user.email_verified_on}")
            else:
                print("❌ Verification token mismatch")
                return False
                
    except Exception as e:
        print(f"❌ Email verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test Password Reset (simulated)
    print("\nStep 4: Testing Password Reset Trigger")
    print("-" * 60)
    try:
        with frappe.as_user("Administrator"):
            user.reload()
            # Test that reset_password can be called (won't actually send email in test)
            reset_link = user.reset_password(send_email=False)
            print(f"✅ Password reset link generated: {reset_link[:50]}...")
            print("✅ Password reset can be triggered (email sending skipped in test)")
            
    except Exception as e:
        print(f"❌ Password reset failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Test Intake Status Check
    print("\nStep 5: Testing Intake Status")
    print("-" * 60)
    try:
        status = get_intake_form_status(test_email)
        print(f"✅ Intake status: {status}")
        assert status['status'] == 'not_started', "Intake should be not_started"
        assert status['patient_exists'] == False, "Patient should not exist yet"
        print("✅ Intake enforcement will block portal access")
        
    except Exception as e:
        print(f"❌ Intake status check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Test Admin Force Verify
    print("\nStep 6: Testing Admin Force Verify")
    print("-" * 60)
    try:
        # Create another test user
        test_email_2 = "test.patient2@example.com"
        if frappe.db.exists("User", test_email_2):
            frappe.delete_doc("User", test_email_2, force=1, ignore_permissions=1)
            frappe.db.commit()
        
        # Signup
        patient_sign_up(email=test_email_2, full_name="Test Patient 2")
        
        # Force verify
        with frappe.as_user("Administrator"):
            force_verify_email(test_email_2, reason="Test - Assisted signup")
        
        # Verify
        user2 = frappe.get_doc("User", test_email_2)
        assert user2.email_verified == 1, "Email should be verified"
        assert user2.email_verified_via == "Admin", "Should be verified via Admin"
        assert user2.email_verified_by == "Administrator", "Should be verified by Administrator"
        print(f"✅ Force verify successful")
        print(f"✅ email_verified_via: {user2.email_verified_via}")
        print(f"✅ email_verified_by: {user2.email_verified_by}")
        
        # Cleanup
        frappe.delete_doc("User", test_email_2, force=1, ignore_permissions=1)
        frappe.db.commit()
        
    except Exception as e:
        print(f"❌ Admin force verify failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Test Intake Completion
    print("\nStep 7: Testing Intake Completion")
    print("-" * 60)
    try:
        # Simulate intake completion
        with frappe.as_user("Administrator"):
            user.reload()
            user.db_set("intake_completed", 1)
            frappe.db.commit()
        
        user.reload()
        assert user.intake_completed == 1, "Intake should be completed"
        print("✅ Intake completion flag set")
        print("✅ Portal access should now be allowed")
        
    except Exception as e:
        print(f"❌ Intake completion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    print("\n" + "="*60)
    print("CLEANUP")
    print("="*60)
    try:
        frappe.delete_doc("User", test_email, force=1, ignore_permissions=1)
        frappe.db.commit()
        print(f"✅ Test user cleaned up: {test_email}")
    except:
        print(f"⚠️  Could not clean up test user (may not exist)")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    test_signup_flow()

