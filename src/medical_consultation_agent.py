import sys
import os
from pathlib import Path
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google

from agents.medical_agents import TriageAgent, SupportAgent, BillingAgent
from services.session_manager import session_manager
from models.medical_models import Patient, UrgencyLevel
from utils.logger import get_logger, LogExecutionTime, log_function_call

load_dotenv()

# Initialize logger
logger = get_logger("MedicalConsultationAgent")

class MedicalConsultationAgent(Agent):
    """Main orchestrator for the medical voice agent system"""
    
    def __init__(self, room_name: str = None, user_id: str = None) -> None:
        logger.info(f"Initializing MedicalConsultationAgent for user: {user_id}, room: {room_name}")
        
        self.room_name = room_name
        self.user_id = user_id
        self.current_agent = None
        self.session = None
        
        # Initialize session
        if user_id and room_name:
            self.session = session_manager.create_session(
                user_id=user_id,
                room_name=room_name,
                initial_context={"entry_time": datetime.now().isoformat()}
            )
        
        # Load configurations
        self.prompts = self._load_prompts()
        
        # Initialize with triage agent (entry point)
        self.triage_agent = TriageAgent(self.session.session_id if self.session else None)
        self.support_agent = None
        self.billing_agent = None
        self.current_agent = self.triage_agent
        
        # Build main instructions
        instructions = self._build_main_instructions()
        super().__init__(instructions=instructions)
        
        logger.debug("MedicalConsultationAgent initialized successfully")
    
    def _load_prompts(self):
        """Load prompts configuration"""
        config_path = Path(__file__).parent / "configs" / "medical_prompts.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load prompts from {config_path}", exc_info=True)
            raise
    
    def _build_main_instructions(self) -> str:
        """Build main agent instructions"""
        return """
        You are the main coordinator for a medical office triage system. You manage three specialized agents:
        
        1. TRIAGE AGENT - Initial assessment and routing (ACTIVE BY DEFAULT)
        2. SUPPORT AGENT - Appointments, prescriptions, professional recommendations
        3. BILLING AGENT - Subscriptions, payments, billing inquiries
        
        WORKFLOW:
        - Start with triage agent for all new conversations
        - Route to appropriate agent based on patient needs
        - Handle transfers between agents smoothly
        - Maintain conversation context across agents
        
        CURRENT AGENT: Triage (assessing patient needs)
        
        Always prioritize patient safety and provide clear, helpful guidance.
        """
    
    @log_function_call()
    def transfer_to_agent(self, agent_type: str, context: Dict[str, Any] = None) -> bool:
        """Transfer conversation to a specific agent"""
        try:
            logger.info(f"Transferring to {agent_type} agent")
            
            if agent_type == "support":
                if not self.support_agent:
                    self.support_agent = SupportAgent(self.session.session_id if self.session else None)
                self.current_agent = self.support_agent
                
            elif agent_type == "billing":
                if not self.billing_agent:
                    self.billing_agent = BillingAgent(self.session.session_id if self.session else None)
                self.current_agent = self.billing_agent
                
            elif agent_type == "triage":
                self.current_agent = self.triage_agent
                
            else:
                logger.warning(f"Unknown agent type: {agent_type}")
                return False
            
            # Update session context
            if self.session:
                session_manager.update_context(
                    self.session.session_id,
                    {
                        "current_agent": agent_type,
                        "transfer_time": datetime.now().isoformat(),
                        "transfer_context": context or {}
                    }
                )
            
            logger.info(f"Successfully transferred to {agent_type} agent")
            return True
            
        except Exception as e:
            logger.error(f"Error transferring to {agent_type} agent: {e}")
            return False
    
    @log_function_call()
    def process_patient_input(self, user_input: str) -> str:
        """Process patient input through the current agent"""
        try:
            # Log conversation
            if self.session:
                session_manager.add_conversation_entry(
                    self.session.session_id,
                    "patient",
                    user_input
                )
            
            # Determine if this is a routing request
            routing_keywords = {
                "billing": ["billing", "payment", "subscription", "cost", "insurance", "bill"],
                "support": ["appointment", "schedule", "prescription", "refill", "doctor", "specialist"],
                "emergency": ["emergency", "urgent", "severe", "911", "ambulance"]
            }
            
            user_input_lower = user_input.lower()
            
            # Check for agent transfer requests
            for agent_type, keywords in routing_keywords.items():
                if any(keyword in user_input_lower for keyword in keywords):
                    if agent_type == "emergency":
                        return "This sounds like an emergency. Please call 911 immediately or go to your nearest emergency room."
                    elif agent_type != self.current_agent.__class__.__name__.lower().replace("agent", ""):
                        if self.transfer_to_agent(agent_type):
                            transfer_messages = self.prompts['medical_voice_agent']['conversation_flow']
                            return transfer_messages.get(f"triage_to_{agent_type}", f"I'm connecting you with our {agent_type} specialist.")
            
            # Process with current agent
            if isinstance(self.current_agent, TriageAgent):
                # Extract symptoms from input (simplified - in real implementation, use NLP)
                symptoms = self._extract_symptoms(user_input)
                response = self.current_agent.assess_patient_symptoms(symptoms, user_input)
                
                # Handle transfers based on triage response
                if response.should_transfer and response.transfer_to:
                    self.transfer_to_agent(response.transfer_to)
                
                return response.message
                
            elif isinstance(self.current_agent, SupportAgent):
                return self._handle_support_request(user_input)
                
            elif isinstance(self.current_agent, BillingAgent):
                return self._handle_billing_request(user_input)
            
            return "I'm not sure how to help with that. Let me connect you with a human representative."
            
        except Exception as e:
            logger.error(f"Error processing patient input: {e}")
            return "I'm experiencing a technical issue. Let me connect you with a human representative."
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Extract symptoms from patient input (simplified implementation)"""
        # In a real implementation, this would use NLP/ML for better extraction
        symptom_keywords = [
            "pain", "headache", "fever", "cough", "nausea", "vomiting", "diarrhea",
            "rash", "swelling", "bleeding", "dizziness", "fatigue", "shortness of breath",
            "chest pain", "back pain", "stomach pain", "sore throat", "runny nose"
        ]
        
        text_lower = text.lower()
        found_symptoms = [symptom for symptom in symptom_keywords if symptom in text_lower]
        
        # If no specific symptoms found, return the general description
        if not found_symptoms:
            found_symptoms = [text[:100]]  # First 100 chars as symptom description
        
        return found_symptoms
    
    def _handle_support_request(self, user_input: str) -> str:
        """Handle support agent requests"""
        user_input_lower = user_input.lower()
        
        if "appointment" in user_input_lower or "schedule" in user_input_lower:
            # In real implementation, extract details from input
            from datetime import date, timedelta
            response = self.current_agent.schedule_appointment(
                patient_id=self.user_id or "anonymous",
                preferred_date=date.today() + timedelta(days=1),
                appointment_type="consultation",
                reason=user_input
            )
            return response.message
            
        elif "prescription" in user_input_lower or "refill" in user_input_lower:
            # Extract medication name (simplified)
            medication = "prescribed medication"  # In real implementation, extract from input
            response = self.current_agent.handle_prescription_refill(
                patient_id=self.user_id or "anonymous",
                medication_name=medication
            )
            return response.message
            
        elif "doctor" in user_input_lower or "specialist" in user_input_lower:
            # Extract department (simplified)
            department = "general practice"  # In real implementation, extract from input
            response = self.current_agent.recommend_professional(department)
            return response.message
        
        return "I can help you with appointments, prescriptions, or finding the right healthcare professional. What would you like assistance with?"
    
    def _handle_billing_request(self, user_input: str) -> str:
        """Handle billing agent requests"""
        user_input_lower = user_input.lower()
        
        if "subscription" in user_input_lower:
            if "upgrade" in user_input_lower or "change" in user_input_lower:
                response = self.current_agent.manage_subscription(
                    user_id=self.user_id or "anonymous",
                    action="update",
                    subscription_type="premium"  # In real implementation, extract from input
                )
            else:
                response = self.current_agent.manage_subscription(
                    user_id=self.user_id or "anonymous",
                    action="check"
                )
            return response.message
            
        elif "payment" in user_input_lower or "pay" in user_input_lower:
            # In real implementation, extract payment details
            response = self.current_agent.process_payment(
                user_id=self.user_id or "anonymous",
                amount=50.0,  # Example amount
                payment_method="credit_card",
                description="Monthly subscription"
            )
            return response.message
        
        return "I can help you with subscriptions, payments, and billing questions. What would you like assistance with?"
    
    def get_greeting_message(self) -> str:
        """Get initial greeting message"""
        triage_prompts = self.prompts['medical_voice_agent']['triage_agent']
        greeting = triage_prompts['greeting']['base_message']
        call_to_action = triage_prompts['greeting']['call_to_action']
        return f"{greeting} {call_to_action}"


def extract_user_info_from_room(room_name: str) -> tuple:
    """Extract user information from room name"""
    logger.debug(f"Extracting user info from room name: {room_name}")
    
    try:
        # Expected format: "medical_<user_id>_<session_type>" or similar
        if "_" in room_name:
            parts = room_name.split("_")
            if len(parts) >= 2:
                user_id = parts[1] if parts[0] == "medical" else parts[0]
                logger.info(f"Extracted user ID: {user_id}")
                return user_id, room_name
    except Exception as e:
        logger.warning(f"Failed to extract user info from room name: {room_name}", exc_info=True)
    
    logger.info("Using anonymous user")
    return "anonymous", room_name


async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the medical consultation voice agent"""
    logger.info("Starting medical consultation voice agent entrypoint")
    
    # Extract user information from room context
    room_name = ctx.room.name if ctx.room else "default_medical_room"
    user_id, room_name = extract_user_info_from_room(room_name)
    
    logger.info(f"Starting medical consultation - Room: {room_name}, User: {user_id}")
    
    try:
        # Create medical consultation agent
        medical_agent = MedicalConsultationAgent(room_name=room_name, user_id=user_id)
        
        # Create session with Google Realtime model
        session = AgentSession(
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Puck",
                temperature=0.7,
                instructions=medical_agent.instructions,
            ),
        )

        await session.start(
            room=ctx.room,
            agent=medical_agent,
            room_input_options=RoomInputOptions(),
        )

        # Send initial greeting
        greeting = medical_agent.get_greeting_message()
        logger.debug(f"Sending greeting: {greeting}")
        await session.generate_reply(instructions=greeting)
        
        logger.info("Medical consultation voice agent session started successfully")
        
    except Exception as e:
        logger.exception("Failed to start medical consultation voice agent session")
        raise


if __name__ == "__main__":
    logger.info("Starting medical consultation voice agent application")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except Exception as e:
        logger.exception("Medical consultation voice agent application failed to start")
        raise