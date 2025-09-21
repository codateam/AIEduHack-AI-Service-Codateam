import sys
import os
from pathlib import Path
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from dataclasses import dataclass
# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from livekit.agents import Agent
from medical_models import UrgencyLevel, TriageResponse, SupportResponse, BillingResponse, AppointmentRequest, PrescriptionRefillRequest, SubscriptionType

from medical_tools import TriageTools, SupportTools, BillingTools
from session_manager import session_manager
from utils.logger import logger









def load_yaml(file_path: str):
    """Load medical configuration from YAML files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            logger.debug(f"Loading {file_path}")
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Failed to load {file_path}", exc_info=True)
        raise

class TriageAgent(Agent):
    """Medical Triage Agent - Initial point of contact for patient assessment"""
    
    def __init__(self, session_id: str = None) -> None:
        logger.info("Initializing TriageAgent")
        
        self.session_id = session_id
        self.agent_config = load_medical_config("agents")
        self.prompts = load_medical_config("prompts")
        
        # Build instructions from config
        instructions = self._build_instructions()
        super().__init__(instructions=instructions)
        
        # Update session with current agent
        if self.session_id:
            session_manager.set_current_agent(self.session_id, "triage")
        
        logger.debug("TriageAgent initialized successfully")
    
    def _build_instructions(self) -> str:
        """Build agent instructions from configuration"""
        config = self.agent_config['triage_agent']
        prompts = self.prompts['medical_voice_agent']['triage_agent']
        
        instructions = f"""
        {config['role']}
        
        GOAL: {config['goal']}
        
        BACKGROUND: {config['backstory']}
        
        INSTRUCTIONS: {config['instructions']}
        
        CONVERSATION GUIDELINES:
        - Start with: "{prompts['greeting']['base_message']}"
        - Ask: "{prompts['greeting']['call_to_action']}"
        - Use follow-up questions to gather complete symptom information
        - Assess urgency level and route appropriately
        - Always prioritize patient safety
        
        AVAILABLE TOOLS:
        - assess_urgency: Evaluate symptom urgency
        - recommend_department: Suggest appropriate medical department
        - create_triage_assessment: Complete triage evaluation
        """
        
        return instructions
    
    def assess_patient_symptoms(self, symptoms: List[str], additional_info: str = "") -> TriageResponse:
        """Assess patient symptoms and determine next steps"""
        try:
            # Create triage assessment using tools
            assessment_result = TriageTools.create_triage_assessment(
                patient_id=self.session_id or "anonymous",
                symptoms=symptoms,
                additional_info=additional_info
            )
            
            if not assessment_result.success:
                return TriageResponse(
                    message="I'm having trouble processing your symptoms. Let me connect you with a human representative.",
                    urgency_assessment=UrgencyLevel.MEDIUM,
                    requires_human_intervention=True
                )
            
            assessment = assessment_result.result
            urgency = UrgencyLevel(assessment['urgency_level'])
            
            # Determine response based on urgency
            prompts = self.prompts['medical_voice_agent']['triage_agent']['routing_messages']
            
            if urgency == UrgencyLevel.EMERGENCY:
                message = prompts['emergency']
                transfer_to = "emergency"
            elif urgency == UrgencyLevel.HIGH:
                message = prompts['high_urgency']
                transfer_to = "support"
            elif urgency == UrgencyLevel.MEDIUM:
                message = prompts['medium_urgency']
                transfer_to = "support"
            else:
                message = prompts['low_urgency']
                transfer_to = "support"
            
            # Log assessment in session
            if self.session_id:
                session_manager.add_conversation_entry(
                    self.session_id,
                    "triage_agent",
                    f"Assessment: {urgency.value} urgency - {assessment['recommended_action']}",
                    {"assessment": assessment}
                )
            
            return TriageResponse(
                message=message,
                urgency_assessment=urgency,
                recommended_department=assessment.get('recommended_department'),
                should_transfer=urgency != UrgencyLevel.EMERGENCY,
                transfer_to=transfer_to,
                actions_taken=[f"Completed triage assessment: {assessment['assessment_id']}"]
            )
            
        except Exception as e:
            logger.error(f"Error in assess_patient_symptoms: {e}")
            return TriageResponse(
                message="I'm experiencing a technical issue. Let me connect you with a human representative.",
                urgency_assessment=UrgencyLevel.MEDIUM,
                requires_human_intervention=True
            )

class SupportAgent(Agent):
    """Medical Support Agent - Handles appointments, prescriptions, and professional recommendations"""
    
    def __init__(self, session_id: str = None) -> None:
        logger.info("Initializing SupportAgent")
        
        self.session_id = session_id
        self.agent_config = load_medical_config("agents")
        self.prompts = load_medical_config("prompts")
        
        # Build instructions from config
        instructions = self._build_instructions()
        super().__init__(instructions=instructions)
        
        # Update session with current agent
        if self.session_id:
            session_manager.set_current_agent(self.session_id, "support")
        
        logger.debug("SupportAgent initialized successfully")
    
    def _build_instructions(self) -> str:
        """Build agent instructions from configuration"""
        config = self.agent_config['support_agent']
        prompts = self.prompts['medical_voice_agent']['support_agent']
        
        instructions = f"""
        {config['role']}
        
        GOAL: {config['goal']}
        
        BACKGROUND: {config['backstory']}
        
        INSTRUCTIONS: {config['instructions']}
        
        CONVERSATION GUIDELINES:
        - Greet with: "{prompts['greeting']['base_message']}"
        - If transferred from triage: "{prompts['greeting']['from_triage']}"
        - Help with appointment scheduling, prescription refills, and professional recommendations
        - Always confirm details before finalizing appointments
        
        AVAILABLE TOOLS:
        - find_available_professionals: Search for healthcare professionals
        - schedule_appointment: Book patient appointments
        - process_prescription_refill: Handle prescription refills
        """
        
        return instructions
    

    def schedule_appointment(self, patient_id: str, preferred_date: date, 
                           appointment_type: str, department: str = None, 
                           reason: str = "", urgency: str = "low") -> SupportResponse:
        """Schedule an appointment for a patient"""
        try:
            # Create appointment request
            appointment_request = AppointmentRequest(
                patient_id=patient_id,
                preferred_date=preferred_date,
                appointment_type=appointment_type,
                department=department,
                reason=reason,
                urgency_level=UrgencyLevel(urgency)
            )
            
            # Schedule using tools
            result = SupportTools.schedule_appointment(appointment_request)
            
            if result.success:
                appointment = result.result
                prompts = self.prompts['medical_voice_agent']['support_agent']['appointment_scheduling']
                
                message = prompts['confirmation'].format(
                    doctor_name=f"Dr. {appointment['doctor_id']}",  # In real app, would lookup doctor name
                    date=appointment['appointment_date'],
                    time=appointment['appointment_date']
                )
                
                # Log in session
                if self.session_id:
                    session_manager.add_conversation_entry(
                        self.session_id,
                        "support_agent",
                        f"Scheduled appointment: {appointment['appointment_id']}",
                        {"appointment": appointment}
                    )
                
                return SupportResponse(
                    message=message,
                    appointment_scheduled=appointment['appointment_id'],
                    actions_taken=[f"Scheduled appointment for {preferred_date}"]
                )
            else:
                return SupportResponse(
                    message=f"I'm having trouble scheduling your appointment: {result.error_message}",
                    requires_human_intervention=True
                )
                
        except Exception as e:
            logger.error(f"Error in schedule_appointment: {e}")
            return SupportResponse(
                message="I'm experiencing a technical issue with scheduling. Let me connect you with a human representative.",
                requires_human_intervention=True
            )
    
    def handle_prescription_refill(self, patient_id: str, medication_name: str, 
                                 pharmacy: str = None) -> SupportResponse:
        """Handle prescription refill request"""
        try:
            refill_request = PrescriptionRefillRequest(
                patient_id=patient_id,
                medication_name=medication_name,
                pharmacy_preference=pharmacy
            )
            
            result = SupportTools.process_prescription_refill(refill_request)
            
            if result.success:
                prompts = self.prompts['medical_voice_agent']['support_agent']['prescription_handling']
                
                if result.result['status'] == 'approved':
                    message = prompts['refill_approved'].format(
                        pharmacy=result.result.get('pharmacy', 'your preferred pharmacy')
                    )
                    prescription_id = result.result.get('prescription_id')
                else:
                    message = prompts['refill_denied']
                    prescription_id = None
                
                # Log in session
                if self.session_id:
                    session_manager.add_conversation_entry(
                        self.session_id,
                        "support_agent",
                        f"Processed prescription refill: {medication_name}",
                        {"refill_result": result.result}
                    )
                
                return SupportResponse(
                    message=message,
                    prescription_processed=prescription_id,
                    actions_taken=[f"Processed refill request for {medication_name}"]
                )
            else:
                return SupportResponse(
                    message=f"I'm having trouble processing your prescription refill: {result.error_message}",
                    requires_human_intervention=True
                )
                
        except Exception as e:
            logger.error(f"Error in handle_prescription_refill: {e}")
            return SupportResponse(
                message="I'm experiencing a technical issue with prescription processing. Let me connect you with a human representative.",
                requires_human_intervention=True
            )
    
    def recommend_professional(self, department: str, date_needed: date = None) -> SupportResponse:
        """Recommend healthcare professionals"""
        try:
            result = SupportTools.find_available_professionals(department, date_needed)
            
            if result.success and result.result:
                professionals = result.result
                prompts = self.prompts['medical_voice_agent']['support_agent']['professional_recommendations']
                
                # Format professional recommendations
                recommendations = []
                for prof in professionals[:3]:  # Limit to top 3
                    recommendations.append(
                        f"Dr. {prof['name']} - {prof['specialization']} (${prof['consultation_fee']})"
                    )
                
                message = prompts['general_inquiry'].format(
                    specialization=department
                ) + "\n" + "\n".join(recommendations)
                
                return SupportResponse(
                    message=message,
                    professional_recommended=professionals[0]['id'],
                    actions_taken=[f"Found {len(professionals)} professionals in {department}"]
                )
            else:
                return SupportResponse(
                    message=f"I couldn't find available professionals in {department} at this time. Let me connect you with someone who can help.",
                    requires_human_intervention=True
                )
                
        except Exception as e:
            logger.error(f"Error in recommend_professional: {e}")
            return SupportResponse(
                message="I'm experiencing a technical issue finding professionals. Let me connect you with a human representative.",
                requires_human_intervention=True
            )

class BillingAgent(Agent):
    """Medical Billing Agent - Handles subscriptions, payments, and billing inquiries"""
    
    def __init__(self, session_id: str = None) -> None:
        logger.info("Initializing BillingAgent")
        
        self.session_id = session_id
        self.agent_config = load_medical_config("agents")
        self.prompts = load_medical_config("prompts")
        
        # Build instructions from config
        instructions = self._build_instructions()
        super().__init__(instructions=instructions)
        
        # Update session with current agent
        if self.session_id:
            session_manager.set_current_agent(self.session_id, "billing")
        
        logger.debug("BillingAgent initialized successfully")
    
    def _build_instructions(self) -> str:
        """Build agent instructions from configuration"""
        config = self.agent_config['billing_agent']
        prompts = self.prompts['medical_voice_agent']['billing_agent']
        
        instructions = f"""
        {config['role']}
        
        GOAL: {config['goal']}
        
        BACKGROUND: {config['backstory']}
        
        INSTRUCTIONS: {config['instructions']}
        
        CONVERSATION GUIDELINES:
        - Greet with: "{prompts['greeting']['base_message']}"
        - Ask: "{prompts['greeting']['call_to_action']}"
        - Handle subscription management, payments, and billing questions
        - Always be transparent about costs and options
        
        AVAILABLE TOOLS:
        - get_subscription_info: Retrieve user subscription details
        - update_subscription: Modify or create subscriptions
        - process_payment: Handle payment processing
        """
        
        return instructions
    

    def manage_subscription(self, user_id: str, action: str, subscription_type: str = None) -> BillingResponse:
        """Manage user subscriptions"""
        try:
            if action == "check":
                result = BillingTools.get_subscription_info(user_id)
                
                if result.success:
                    if 'subscription_type' in result.result:
                        subscription = result.result
                        prompts = self.prompts['medical_voice_agent']['billing_agent']['subscription_management']
                        
                        message = prompts['current_status'].format(
                            subscription_type=subscription['subscription_type'],
                            features=", ".join(subscription['features']),
                            next_billing=subscription.get('end_date', 'Next month')
                        )
                    else:
                        message = result.result['message']
                    
                    return BillingResponse(
                        message=message,
                        actions_taken=[f"Retrieved subscription info for user {user_id}"]
                    )
                
            elif action == "update" and subscription_type:
                result = BillingTools.update_subscription(user_id, SubscriptionType(subscription_type))
                
                if result.success:
                    subscription = result.result
                    action_taken = subscription['action']
                    
                    message = f"Your subscription has been {action_taken} successfully. "
                    message += f"You now have {subscription['subscription_type']} access with features: {', '.join(subscription['features'])}"
                    
                    # Log in session
                    if self.session_id:
                        session_manager.add_conversation_entry(
                            self.session_id,
                            "billing_agent",
                            f"Subscription {action_taken}: {subscription_type}",
                            {"subscription": subscription}
                        )
                    
                    return BillingResponse(
                        message=message,
                        subscription_updated=subscription['subscription_id'],
                        actions_taken=[f"Subscription {action_taken} to {subscription_type}"]
                    )
            
            return BillingResponse(
                message="I need more information to help with your subscription. Could you clarify what you'd like to do?",
                requires_human_intervention=False
            )
            
        except Exception as e:
            logger.error(f"Error in manage_subscription: {e}")
            return BillingResponse(
                message="I'm experiencing a technical issue with subscription management. Let me connect you with a human representative.",
                requires_human_intervention=True
            )
    

    def process_payment(self, user_id: str, amount: float, payment_method: str, description: str = "") -> BillingResponse:
        """Process a payment"""
        try:
            result = BillingTools.process_payment(user_id, amount, payment_method, description)
            
            if result.success:
                payment = result.result
                prompts = self.prompts['medical_voice_agent']['billing_agent']['payment_processing']
                
                message = prompts['payment_confirmation'].format(amount=amount)
                
                # Log in session
                if self.session_id:
                    session_manager.add_conversation_entry(
                        self.session_id,
                        "billing_agent",
                        f"Payment processed: ${amount}",
                        {"payment": payment}
                    )
                
                return BillingResponse(
                    message=message,
                    payment_processed=payment['payment_id'],
                    actions_taken=[f"Processed payment of ${amount}"]
                )
            else:
                prompts = self.prompts['medical_voice_agent']['billing_agent']['payment_processing']
                return BillingResponse(
                    message=prompts['payment_failed'],
                    requires_human_intervention=True
                )
                
        except Exception as e:
            logger.error(f"Error in process_payment: {e}")
            return BillingResponse(
                message="I'm experiencing a technical issue with payment processing. Let me connect you with a human representative.",
                requires_human_intervention=True
            )