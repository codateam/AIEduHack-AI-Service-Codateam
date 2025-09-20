import os
import yaml
from livekit.agents import Agent, AgentSession, ChatContext, function_tool, get_job_context, RunContext, JobContext, WorkerOptions, cli
# from livekit.plugins import cartesia
from dataclasses import dataclass
from typing import Optional
from livekit.plugins import google, openai, deepgram, cartesia, silero

from dotenv import load_dotenv


load_dotenv()
# Define the session state to store patient information
@dataclass
class MedicalSessionInfo:
    patient_name: str | None = None
    age: int | None = None
    recording_consent: bool = False
    symptoms: list[str] = None
    medical_history: str | None = None
    emergency_level: str | None = None  # "low", "medium", "high", "emergency"
    recommended_specialty: str | None = None
    specialty_confidence: str | None = None  # "high", "medium", "low"
    
    def __post_init__(self):
        if self.symptoms is None:
            self.symptoms = []

RunContext_T = RunContext[MedicalSessionInfo]

# Load specialty configuration
def load_specialty_config():
    """Load specialty determination configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'configs', 'specialty_prompts.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        # Fallback configuration if file not found
        return {
            'specialty_determination': {
                'specialties': {
                    'general_medicine': {
                        'name': 'General Medicine',
                        'description': 'General health concerns and preventive care'
                    }
                }
            }
        }


class ConsentCollectorAgent(Agent):
    """First agent that collects recording consent before proceeding"""
    
    def __init__(self):
        super().__init__(
            instructions="""You are a voice AI agent with the singular task to collect positive 
            recording consent from the user for a medical consultation. You must be polite but 
            clear that consent is required. If consent is not given, you must end the call."""
        )

    async def on_enter(self) -> None:
        await self.session.say(
            "Hello, welcome to Teracare For quality assurance and "
            "medical record purposes, may I have your consent to record this consultation?"
        )

    @function_tool()
    async def on_consent_given(self, context: RunContext_T):
        """Use this tool when the patient gives consent to record."""
        context.userdata.recording_consent = True
        await self.session.say("Thank you for your consent. Let me connect you with our intake specialist.")
        
        # Hand off to intake agent with current chat context
        return IntakeAgent()

    @function_tool()
    async def end_call(self) -> None:
        """Use this tool when consent is not given and the call should end."""
        await self.session.say(
            "I understand. Without recording consent, we cannot proceed with the medical consultation. "
            "Please feel free to call back if you change your mind. Have a wonderful day."
        )
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(api.DeleteRoomRequest(room=job_ctx.room.name))

class IntakeAgent(Agent):
    """Second agent that collects basic patient information"""
    
    def __init__(self, chat_ctx: ChatContext = None):
        super().__init__(
            instructions="""You are a medical intake specialist. Your job is to collect the patient's 
            basic information: name, age, and primary symptoms. Be empathetic and professional. 
            Collect one piece of information at a time.""",
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        await self.session.say(
            "I'm your intake specialist. To help provide you with the best care, "
            "I need to collect some basic information. May I start with your name?"
        )
        
    @function_tool()
    async def record_name(self, context: RunContext_T, name: str):
        """Record the patient's name."""
        context.userdata.patient_name = name.strip()
        await self.session.say(f"Thank you, {name}. Now, may I have your age?")
        return self._check_handoff_ready()
    
    @function_tool()
    async def record_age(self, context: RunContext_T, age: int):
        """Record the patient's age."""
        if age < 0 or age > 120:
            await self.session.say("That doesn't seem like a valid age. Could you please repeat your age?")
            return None
            
        context.userdata.age = age
        await self.session.say("Thank you. Now, can you briefly describe your main symptoms or concerns?")
        return self._check_handoff_ready()
    
    @function_tool()
    async def record_symptoms(self, context: RunContext_T, symptoms: str):
        """Record the patient's primary symptoms."""
        context.userdata.symptoms.append(symptoms.strip())
        await self.session.say("I've noted your symptoms. Let me connect you with our triage specialist.")
        return self._check_handoff_ready()
    
    def _check_handoff_ready(self):
        """Check if we have enough information to hand off to triage"""
        userdata = self.session.userdata
        if userdata.patient_name and userdata.age and userdata.symptoms:
            return TriageAgent()
        return None

class TriageAgent(Agent):
    """Third agent that assesses urgency and collects detailed medical information"""
    
    def __init__(self, chat_ctx: ChatContext = None):
        super().__init__(
            instructions="""You are a medical triage specialist. Based on the patient's symptoms, 
            assess the urgency level and collect relevant medical history. Ask about:
            - Duration and severity of symptoms
            - Current medications
            - Allergies
            - Previous medical conditions
            - Recent changes in symptoms
            
            Categorize urgency as: emergency (immediate care), high (same day), medium (within 2-3 days), 
            or low (routine appointment).""",
            chat_ctx=chat_ctx,
            # Use a different voice for the triage specialist
            tts=cartesia.TTS(voice="6f84f4b8-58a2-430c-8c79-688dad597532")
        )

    async def on_enter(self) -> None:
        userdata: MedicalSessionInfo = self.session.userdata
        await self.session.say(
            f"Hello {userdata.patient_name}, I'm your triage specialist. I need to assess "
            f"the urgency of your symptoms and gather some medical history."
        )

    @function_tool()
    async def record_medical_history(self, context: RunContext_T, history: str):
        """Record relevant medical history, medications, allergies, etc."""
        context.userdata.medical_history = history.strip()
        await self.session.say("Thank you for that information. Let me assess your situation.")
        return None

    @function_tool()
    async def set_emergency_level(self, context: RunContext_T, level: str, reasoning: str):
        """Set the emergency/urgency level based on symptoms assessment.
        
        Args:
            level: Must be one of 'emergency', 'high', 'medium', 'low'
            reasoning: Explanation for the urgency level
        """
        valid_levels = ['emergency', 'high', 'medium', 'low']
        if level.lower() not in valid_levels:
            await self.session.say("I need to reassess the urgency level. Let me gather more information.")
            return None
            
        context.userdata.emergency_level = level.lower()
        
        if level.lower() == 'emergency':
            await self.session.say(
                f"Based on your symptoms, this requires immediate emergency care. {reasoning} "
                "I'm connecting you with emergency services coordination."
            )
            return EmergencyAgent()
        else:
            await self.session.say(
                f"I've assessed your condition as {level} priority. {reasoning} "
                "Now let me connect you with our specialty determination specialist."
            )
            return SpecialtyDeterminationAgent()

class SpecialtyDeterminationAgent(Agent):
    """Agent that helps determine the appropriate medical specialty based on symptoms"""
    
    def __init__(self, chat_ctx: ChatContext = None):
        # Load specialty configuration
        self.specialty_config = load_specialty_config()['specialty_determination']
        
        super().__init__(
            instructions=f"""You are a medical specialty determination specialist. Your role is to:
            1. Analyze patient symptoms and medical history
            2. Ask targeted questions to clarify symptoms
            3. Recommend the most appropriate medical specialty
            4. Explain your recommendation clearly
            
            Available specialties: {', '.join(self.specialty_config['specialties'].keys())}
            
            Be thorough but efficient in your assessment. Ask follow-up questions only when necessary 
            to make an accurate specialty recommendation.""",
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: MedicalSessionInfo = self.session.userdata
        greeting = self.specialty_config['prompts']['greeting']
        await self.session.say(
            f"Hello {userdata.patient_name}, {greeting}"
        )
        
        # Start assessment
        assessment_intro = self.specialty_config['prompts']['assessment_intro']
        await self.session.say(assessment_intro)

    @function_tool()
    async def ask_clarifying_question(self, context: RunContext_T, question: str):
        """Ask a clarifying question to better understand the patient's condition."""
        await self.session.say(question)
        return None

    @function_tool()
    async def determine_specialty(self, context: RunContext_T, specialty: str, confidence: str, reasoning: str):
        """Determine the recommended medical specialty.
        
        Args:
            specialty: The recommended specialty (must match available specialties)
            confidence: Confidence level - 'high', 'medium', or 'low'
            reasoning: Explanation for the specialty recommendation
        """
        available_specialties = list(self.specialty_config['specialties'].keys())
        
        if specialty.lower() not in [s.lower() for s in available_specialties]:
            await self.session.say("Let me reassess your symptoms to make a better recommendation.")
            return None
            
        valid_confidence = ['high', 'medium', 'low']
        if confidence.lower() not in valid_confidence:
            confidence = 'medium'
            
        # Store the recommendation
        context.userdata.recommended_specialty = specialty.lower()
        context.userdata.specialty_confidence = confidence.lower()
        
        # Get specialty information
        specialty_info = self.specialty_config['specialties'].get(specialty.lower(), {})
        specialty_name = specialty_info.get('name', specialty)
        specialty_description = specialty_info.get('description', '')
        
        # Provide recommendation
        if confidence.lower() == 'high':
            recommendation_msg = self.specialty_config['prompts']['specialty_recommendation'].format(
                specialty_name=specialty_name,
                specialty_description=specialty_description
            )
        else:
            recommendation_msg = self.specialty_config['prompts']['general_medicine_recommendation']
            
        await self.session.say(f"{recommendation_msg} {reasoning}")
        
        # Hand off to care coordinator
        handoff_msg = self.specialty_config['prompts']['handoff_message'].format(
            specialty_name=specialty_name
        )
        await self.session.say(handoff_msg)
        
        return CareCoordinatorAgent()

    @function_tool()
    async def recommend_multiple_specialties(self, context: RunContext_T, 
                                           primary_specialty: str, secondary_specialty: str, reasoning: str):
        """Recommend multiple specialties when symptoms span multiple areas.
        
        Args:
            primary_specialty: The primary recommended specialty
            secondary_specialty: The secondary recommended specialty
            reasoning: Explanation for multiple specialty recommendation
        """
        available_specialties = list(self.specialty_config['specialties'].keys())
        
        if (primary_specialty.lower() not in [s.lower() for s in available_specialties] or 
            secondary_specialty.lower() not in [s.lower() for s in available_specialties]):
            await self.session.say("Let me reassess your symptoms to make a better recommendation.")
            return None
            
        # Store primary specialty
        context.userdata.recommended_specialty = primary_specialty.lower()
        context.userdata.specialty_confidence = 'medium'
        
        # Get specialty information
        primary_info = self.specialty_config['specialties'].get(primary_specialty.lower(), {})
        secondary_info = self.specialty_config['specialties'].get(secondary_specialty.lower(), {})
        
        primary_name = primary_info.get('name', primary_specialty)
        secondary_name = secondary_info.get('name', secondary_specialty)
        
        # Provide recommendation
        recommendation_msg = self.specialty_config['prompts']['multiple_specialties'].format(
            primary_specialty=primary_name,
            secondary_specialty=secondary_name
        )
        
        await self.session.say(f"{recommendation_msg} {reasoning}")
        
        # Hand off to care coordinator
        handoff_msg = self.specialty_config['prompts']['handoff_message'].format(
            specialty_name=primary_name
        )
        await self.session.say(handoff_msg)
        
        return CareCoordinatorAgent()

class EmergencyAgent(Agent):
    """Handles emergency situations requiring immediate care"""
    
    def __init__(self, chat_ctx: ChatContext = None):
        super().__init__(
            instructions="""You are an emergency care coordinator. Your job is to:
            1. Confirm the patient's location
            2. Provide immediate safety instructions
            3. Coordinate emergency services if needed
            4. Stay on the line until help arrives
            
            Be calm, clear, and directive.""",
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: MedicalSessionInfo = self.session.userdata
        await self.session.say(
            f"{userdata.patient_name}, this is an emergency situation. "
            "I need your exact location so we can send help immediately."
        )

    @function_tool()
    async def record_location(self, context: RunContext_T, location: str):
        """Record the patient's current location for emergency services."""
        await self.session.say(
            f"Emergency services are being contacted for {location}. "
            "Please stay on the line. Do not hang up."
        )
        # In a real implementation, this would trigger actual emergency services
        return None

    @function_tool()
    async def provide_immediate_care_instructions(self, instructions: str):
        """Provide immediate care instructions while waiting for emergency services."""
        await self.session.say(f"While we wait for help: {instructions}")
        return None

class CareCoordinatorAgent(Agent):
    """Final agent that provides care recommendations and next steps"""
    
    def __init__(self, chat_ctx: ChatContext = None):
        super().__init__(
            instructions="""You are a care coordinator. Based on the patient's assessed priority level, 
            provide appropriate next steps:
            - High priority: Schedule urgent appointment or direct to urgent care
            - Medium priority: Schedule appointment within 2-3 days
            - Low priority: Routine appointment scheduling or self-care advice
            
            Always provide clear next steps and contact information.""",
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: MedicalSessionInfo = self.session.userdata
        specialty_info = f" for {userdata.recommended_specialty}" if userdata.recommended_specialty else ""
        await self.session.generate_reply(
            instructions=f"""Greet {userdata.patient_name} and provide care recommendations based on their 
            {userdata.emergency_level} priority assessment{specialty_info}. Give specific next steps for scheduling 
            and follow-up care."""
        )

    @function_tool()
    async def schedule_appointment(self, context: RunContext_T, 
                                 appointment_type: str, timeframe: str):
        """Schedule an appointment for the patient."""
        userdata = context.userdata
        specialty_detail = ""
        if userdata.recommended_specialty:
            specialty_detail = f" with a {userdata.recommended_specialty} specialist"
        
        await self.session.say(
            f"I'm scheduling a {appointment_type} appointment{specialty_detail} for you within {timeframe}. "
            f"You'll receive a confirmation shortly."
        )
        return None

    @function_tool()
    async def provide_self_care_instructions(self, instructions: str):
        """Provide self-care instructions for non-urgent conditions."""
        await self.session.say(f"Here are some self-care instructions: {instructions}")
        return None

    @function_tool()
    async def end_consultation(self, context: RunContext_T):
        """End the consultation with summary and next steps."""
        userdata = context.userdata
        await self.session.say(
            f"Thank you {userdata.patient_name}. Your consultation is complete. "
            "You should receive follow-up information shortly. Take care!"
        )
        return None



async def entrypoint(ctx: JobContext):
    """Main entrypoint for the medical assistance agent system"""
    # Create the medical session
    session = AgentSession[MedicalSessionInfo](
        userdata=MedicalSessionInfo(),
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
        # llm = openai.realtime.RealtimeModel(
        # voice="shimmer",
        # temperature=0.8,
        # modalities=["audio", "text"]
    # )
        # llm=google.beta.realtime.RealtimeModel(
        #     model="gemini-2.0-flash-exp",
        #     voice="Puck",
        #     temperature=0.7,
        # ),
    )
    
    # Start with the consent collector agent
    initial_agent = ConsentCollectorAgent()

   
    
    await session.start(
        agent=initial_agent,
        room=ctx.room,
       
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))