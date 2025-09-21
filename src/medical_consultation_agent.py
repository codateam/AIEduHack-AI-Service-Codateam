from dis import Instruction
import sys
import os

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from opentelemetry import context

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext, JobRequest
from livekit.plugins import google, cartesia, deepgram, silero, openai

from medical_agents import TriageAgent, SupportAgent, BillingAgent
from utils.logger import logger
from utils.helper import load_yaml

load_dotenv()

# Initialize logger
logger.info("MedicalConsultationAgent initialized")
instructions = load_yaml(str(project_root / "src" / "configs" / "general_practitioner_prompt.yaml"))


@dataclass
class UserInfo:
    name: str | None = None
    email: str | None = None
    speciality: str | None = None




class MedicalConsultationAgent(Agent):
    """Main orchestrator for the medical voice agent system"""
    
    def __init__(self) -> None:
        logger.info(f"Initializing MedicalConsultationAgent for user")
        super().__init__(instructions="""You are the Medical Office Triage agent. Your job is to determine if the patient needs 
  help with medical support services or billing issues. Ask questions to understand their needs, 
  then transfer them to the appropriate department.
  
  Follow these guidelines:
  - Listen carefully to determine if their issue is related to medical services or billing
  - Ask clarifying questions if needed to properly categorize their request
  - For medical services: general practitioner 
  - Transfer them to the appropriate department once you understand their needs
  - If the patient has multiple issues, address the most urgent concern first
  - Be professional, courteous, and empathetic in your communication
  - Maintain patient confidentiality and follow HIPAA guidelines at all times  """)
        

    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions="Greet the patient warmly and offer your assistance.")

    @function_tool
    async def transfer_to_general_practitioner(self, context: RunContext[UserInfo]):

        """Transfer conversation to the general practitioner agent"""
        try:
            logger.info(f"Transferring to general practitioner agent")
            return GeneralPractitionerAgent(chat_ctx=self.chat_ctx), "transfering to general practitioner agent"
            
        except Exception as e:
            logger.error(f"Error transferring to general practitioner agent: {e}")
            return False

class GeneralPractitionerAgent(Agent):
    """General practitioner that recommend specialty for patient"""

    def __init__(self) -> None:
        logger.info(f"Initializing GeneralPractitioner agent")
        instructions = load_yaml(str(project_root / "src" / "configs" / "general_practitioner_prompt.yaml"))
        logger.info(f"load instructions successfully")
        super().__init__(instructions="""
        role: {role}
        description: {description}
        instructions: {instructions}
        specialist_list: {specialist_list}
        decision_rules: {decision_rules}
        example: {example_flow}

        """.format(**instructions['general_practitioner']))

    async def on_enter(self) -> None:
        logger.info(f"On enter started")
        await self.session.generate_reply(instructions="Greet the patient warmly and offer your assistance.")
        logger.info(f"On enter finished")


    @function_tool
    async def save_recommended_specialty(self, context: RunContext[UserInfo], speciality:str) -> None:
        """Save the recommended speciality into user context and transfer to appointment management agent"""

        context.userdata.speciality = speciality
        await self.session.generate_reply(instructions=f"Your recommended speciality is {speciality}, I will now transfer you to appointment manager")

        
        if speciality:
            return AppointmentManagementAgent(), "transfering to appointment manager"
        else:
            return None, "Failed to transfer to appointment manager"


    # @function_tool
    # async def transfer_to_appointment(self, context: RunContext[UserInfo], specialty: str):
    #     """Transfer conversation to the support agent """
    #     return MedicalConsultationAgent(), "Transfering to support agent"

class AppointmentManagementAgent(Agent):
    """Appointment management agent """
    def __init__(self) -> None:
        instructions = load_yaml(str(project_root / "src" / "configs" / "appointment_management_prompt.yaml"))
        super().__init__(instructions="""
        role: {role}
        description: {description}
        instructions: {instructions}
        available_functions: {available_functions}
        """.format(**instructions['appointment_management']))
    
    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions="Greet the patient warmly and offer your assistance.")

    @function_tool
    async def book_appointment(self, context: RunContext[UserInfo], date: str, time: str, reason: str) -> None:
        """Book an appointment with the patient"""
        await self.session.generate_reply(instructions=f"Appointment booked for {date} at {time} for {reason}")

        return None, "Appointment booked"

    @function_tool
    async def reschedule_appointment(self, context: RunContext[UserInfo], date: str, time: str, reason: str) -> None:
        """Reschedule an appointment with the patient"""
        await self.session.generate_reply(instructions=f"Appointment rescheduled for {date} at {time} for {reason}")

        return None, "Appointment rescheduled"
    
    @function_tool
    async def cancel_appointment(self, context: RunContext[UserInfo], date: str, time: str, reason: str) -> None:
        """Cancel an appointment with the patient"""
        await self.session.generate_reply(instructions=f"Appointment cancelled for {date} at {time} for {reason}")

        return None, "Appointment cancelled"








async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the medical consultation voice agent"""
    logger.info("Starting medical consultation voice agent entrypoint")
    try:        
        session = AgentSession[UserInfo](
            userdata=UserInfo(),
            llm=google.LLM(
                model="gemini-2.0-flash-exp",

            ),
           tts = openai.TTS(
                model="gpt-4o-mini-tts",
                voice="ash",
                instructions="Speak in a friendly and conversational tone.",
            ),
            # llm=openai.LLM(model="gpt-4o-mini"),
            stt = deepgram.STT(
                model="nova-3",
            ),
            # tts=groq.TTS(
            #     model="playai-tts",
            #     voice="Arista-PlayAI", 
            #  ),
            # tts = google.beta.GeminiTTS(
            #     model="gemini-2.5-flash-preview-tts",
            #     voice_name="Zephyr",
            #     instructions="Speak in a friendly and engaging tone.",
            #     ),
            vad=silero.VAD.load(),
            turn_detection="vad",  # Use the simpler, faster, and stable VAD-based turn detection
            # user_away_timeout=60,  # Wait for 60 seconds of silence before ending
        )

        await session.start(
            room=ctx.room,
            agent=MedicalConsultationAgent(),
        )

        await session.generate_reply(instructions="Greet the patient warmly and offer your assistance.")

        logger.info("Medical consultation voice agent session started successfully")
        
    except Exception as e:
        logger.exception("Failed to start medical consultation voice agent session")
        raise

async def request_fnc(req: JobRequest):
    logger.info(f"Accepting job {req.job.id} for open-source agent")
    await req.accept(identity="medical-assistence")


if __name__ == "__main__":
    logger.info("Starting medical consultation voice agent application")
    try:
        agents.cli.run_app(agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,
        ))
    except Exception as e:
        logger.exception("Medical consultation voice agent application failed to start")
        raise