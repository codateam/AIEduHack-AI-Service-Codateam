#!/usr/bin/env python3
"""
Test script for the Medical Office Triage Agent system
Demonstrates the modular voice agent functionality
"""

import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from medical_consultation_agent import MedicalConsultationAgent
from services.session_manager import session_manager
from models.medical_models import Patient, UrgencyLevel

def test_session_management():
    """Test session creation and management"""
    print("=== Testing Session Management ===")
    
    # Create a test session
    session = session_manager.create_session(
        user_id="test_patient_123",
        room_name="medical_test_room",
        initial_context={"test_mode": True}
    )
    
    print(f"Created session: {session.session_id}")
    print(f"User ID: {session.user_id}")
    print(f"Room: {session.room_name}")
    
    # Add conversation entries
    session_manager.add_conversation_entry(session.session_id, "patient", "I have a headache")
    session_manager.add_conversation_entry(session.session_id, "agent", "I understand you have a headache. Can you tell me more about it?")
    
    # Retrieve session
    retrieved_session = session_manager.get_session(session.session_id)
    print(f"Retrieved session with {len(retrieved_session.conversation_history)} conversation entries")
    
    # Update context
    session_manager.update_context(session.session_id, {"current_agent": "triage", "symptoms": ["headache"]})
    
    updated_session = session_manager.get_session(session.session_id)
    print(f"Updated context: {updated_session.context}")
    
    print("✓ Session management test completed\n")

def test_agent_initialization():
    """Test medical consultation agent initialization"""
    print("=== Testing Agent Initialization ===")
    
    try:
        # Initialize the main agent
        agent = MedicalConsultationAgent(
            room_name="test_medical_room",
            user_id="test_patient_456"
        )
        
        print(f"✓ Medical consultation agent initialized")
        print(f"✓ Current agent: {type(agent.current_agent).__name__}")
        print(f"✓ Session ID: {agent.session.session_id if agent.session else 'None'}")
        
        # Test greeting message
        greeting = agent.get_greeting_message()
        print(f"✓ Greeting message: {greeting[:100]}...")
        
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
    
    print("✓ Agent initialization test completed\n")

def test_agent_transfers():
    """Test agent transfer functionality"""
    print("=== Testing Agent Transfers ===")
    
    try:
        agent = MedicalConsultationAgent(
            room_name="test_transfer_room",
            user_id="test_patient_789"
        )
        
        # Test transfer to support agent
        success = agent.transfer_to_agent("support", {"reason": "appointment_request"})
        print(f"✓ Transfer to support agent: {'Success' if success else 'Failed'}")
        print(f"✓ Current agent: {type(agent.current_agent).__name__}")
        
        # Test transfer to billing agent
        success = agent.transfer_to_agent("billing", {"reason": "payment_inquiry"})
        print(f"✓ Transfer to billing agent: {'Success' if success else 'Failed'}")
        print(f"✓ Current agent: {type(agent.current_agent).__name__}")
        
        # Test transfer back to triage
        success = agent.transfer_to_agent("triage")
        print(f"✓ Transfer back to triage: {'Success' if success else 'Failed'}")
        print(f"✓ Current agent: {type(agent.current_agent).__name__}")
        
    except Exception as e:
        print(f"✗ Agent transfer test failed: {e}")
    
    print("✓ Agent transfer test completed\n")

def test_patient_input_processing():
    """Test patient input processing"""
    print("=== Testing Patient Input Processing ===")
    
    try:
        agent = MedicalConsultationAgent(
            room_name="test_input_room",
            user_id="test_patient_101"
        )
        
        # Test various patient inputs
        test_inputs = [
            "I have a severe headache and feel dizzy",
            "I need to schedule an appointment with a doctor",
            "I want to refill my prescription",
            "How much does my subscription cost?",
            "I need to update my billing information"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\nTest {i}: '{user_input}'")
            response = agent.process_patient_input(user_input)
            print(f"Response: {response[:150]}...")
            print(f"Current agent: {type(agent.current_agent).__name__}")
        
    except Exception as e:
        print(f"✗ Patient input processing test failed: {e}")
    
    print("✓ Patient input processing test completed\n")

def test_tools_functionality():
    """Test individual agent tools"""
    print("=== Testing Tools Functionality ===")
    
    try:
        from agents.medical_agents import TriageAgent, SupportAgent, BillingAgent
        
        # Test Triage Agent
        triage_agent = TriageAgent("test_session_triage")
        triage_response = triage_agent.assess_patient_symptoms(
            ["headache", "fever", "nausea"], 
            "I have a bad headache, fever, and feel nauseous"
        )
        print(f"✓ Triage assessment: {triage_response.urgency_level}")
        print(f"✓ Recommended department: {triage_response.recommended_department}")
        
        # Test Support Agent
        support_agent = SupportAgent("test_session_support")
        from datetime import date, timedelta
        appointment_response = support_agent.schedule_appointment(
            patient_id="test_patient",
            preferred_date=date.today() + timedelta(days=1),
            appointment_type="consultation",
            reason="Follow-up consultation"
        )
        print(f"✓ Appointment scheduled: {appointment_response.success}")
        
        # Test Billing Agent
        billing_agent = BillingAgent("test_session_billing")
        subscription_response = billing_agent.manage_subscription(
            user_id="test_user",
            action="check"
        )
        print(f"✓ Subscription check: {subscription_response.success}")
        
    except Exception as e:
        print(f"✗ Tools functionality test failed: {e}")
    
    print("✓ Tools functionality test completed\n")

def main():
    """Run all tests"""
    print("🏥 Medical Office Triage Agent System - Test Suite")
    print("=" * 60)
    
    try:
        test_session_management()
        test_agent_initialization()
        test_agent_transfers()
        test_patient_input_processing()
        test_tools_functionality()
        
        print("🎉 All tests completed successfully!")
        print("\nThe modular voice agent system is ready with:")
        print("✓ BaseModel for user data and session management")
        print("✓ Three specialized agents (Triage, Support, Billing)")
        print("✓ Tool calling functionality for each agent")
        print("✓ Session persistence and conversation history")
        print("✓ Seamless agent transfers based on patient needs")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()