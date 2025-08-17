import sys
import os
from pathlib import Path
import yaml
import asyncio

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import json
import re

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.rtc import ParticipantKind  # Add this import
from livekit.plugins import google
from utils.course_material_service import CourseMaterialService
from utils.logger import get_logger, LogExecutionTime, log_function_call

load_dotenv()

# Initialize logger
logger = get_logger("VoiceAgent")

# User session storage for course context
user_sessions = {}

def load_voice_agent_config():
    """Load voice agent configuration from YAML file"""
    config_path = Path(__file__).parent / "configs" / "voice_agent_config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.warning(f"Voice agent config not found at {config_path}, using defaults")
        return {
            'voice_agent': {
                'connection': {'max_retries': 3, 'retry_delay': 1.0},
                'model': {'name': 'gemini-2.0-flash-exp', 'voice': 'Puck', 'temperature': 0.7},
                'greeting': {'delay_seconds': 1.0, 'fallback_delay_seconds': 2.0}
            }
        }
    except Exception as e:
        logger.error(f"Failed to load voice agent config: {e}")
        raise

async def cleanup_expired_sessions():
    """Clean up expired user sessions"""
    current_time = asyncio.get_event_loop().time()
    expired_sessions = []
    
    for user_id, session_data in user_sessions.items():
        session_start = session_data.get('session_start_time', current_time)
        if current_time - session_start > 3600:  # 1 hour timeout
            expired_sessions.append(user_id)
    
    for user_id in expired_sessions:
        logger.info(f"Cleaning up expired session for user: {user_id}")
        del user_sessions[user_id]

def load_prompts():
    """Load prompts from YAML configuration file"""
    config_path = Path(__file__).parent / "configs" / "prompts.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            logger.debug(f"Loading prompts from {config_path}")
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Failed to load prompts from {config_path}", exc_info=True)
        raise

class TeacherAssistant(Agent):
    def __init__(self, course_id: str = None, course_name: str = None) -> None:
        logger.info(f"Initializing TeacherAssistant for course: {course_name} (ID: {course_id})")
        
        self.course_id = course_id
        self.course_name = self._validate_course_name(course_name)
        self.course_service = self._initialize_course_service()
        self.prompts = load_prompts()
        self.config = load_voice_agent_config()
        
        # Build teaching instructions from YAML config
        teaching_instructions = self._build_teaching_instructions()
        super().__init__(instructions=teaching_instructions)
        
        logger.debug("TeacherAssistant initialized successfully")
    
    def _validate_course_name(self, course_name: str) -> str:
        """Validate and sanitize course name"""
        if not course_name:
            return "the subject"
        
        # Remove potentially problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', course_name.strip())
        return sanitized if sanitized else "the subject"
    
    def _initialize_course_service(self) -> CourseMaterialService:
        """Initialize course service with error handling"""
        try:
            return CourseMaterialService()
        except Exception as e:
            logger.error(f"Failed to initialize course service: {e}")
            # Return a mock service or handle gracefully
            return None

    def _build_teaching_instructions(self) -> str:
        """Build teaching instructions from YAML configuration"""
        logger.debug("Building teaching instructions from YAML config")
        
        config = self.prompts['voice_agent']['teacher_assistant']
        
        # Base instruction
        base = config['base_instruction'].format(course_name=self.course_name)
        
        # Core principles
        principles = "\n".join([f"- {principle}" for principle in config['core_principles']])
        
        # Response format
        response_format = "\n".join([f"- {item}" for item in config['response_format']])
        
        # Interaction style
        interaction_style = "\n".join([f"- {item}" for item in config['interaction_style']])
        
        instructions = f"""{base}

        CORE PRINCIPLES:
        {principles}

        RESPONSE FORMAT:
        {response_format}

        INTERACTION STYLE:
        {interaction_style}"""
        
        logger.debug("Teaching instructions built successfully")
        return instructions

    @log_function_call()
    def get_course_context(self, query: str) -> str:
        """Retrieve relevant course context for the query"""
        error_messages = self.prompts['voice_agent']['error_messages']
        
        if not self.course_id:
            logger.warning("No course ID provided for context retrieval")
            return error_messages['no_course_material']
        
        if not self.course_service:
            logger.error("Course service not available")
            return error_messages['material_unavailable']
        
        try:
            with LogExecutionTime(f"course context query for '{query}'", logger):
                results = self.course_service.query(self.course_id, query)
                
            if results and results.get('documents') and len(results['documents']) > 0:
                # Format context with source IDs
                context_parts = []
                for i, doc in enumerate(results['documents'][0][:3]):  # Limit to top 3 results
                    context_parts.append(f"<id>{i+1}</id>: {doc[:500]}...")  # Truncate for voice
                
                logger.info(f"Retrieved {len(context_parts)} context chunks for query: {query}")
                return "\n".join(context_parts)
            
            logger.info(f"No specific course material found for query: {query}")
            return error_messages['no_specific_material']
            
        except Exception as e:
            logger.exception(f"Error retrieving course context for query: {query}")
            return error_messages['material_unavailable']

    def get_greeting_message(self) -> str:
        """Get initial greeting message"""
        greeting_config = self.prompts['voice_agent']['greeting']
        greeting_instruction = greeting_config['base_message']
        
        if self.course_name and self.course_name != "the subject":
            greeting_instruction += greeting_config['with_course'].format(course_name=self.course_name)
        
        greeting_instruction += greeting_config['call_to_action']
        return greeting_instruction


def extract_course_info_from_room(room_name: str) -> tuple:
    """Extract course_id and course_name from room name or metadata"""
    logger.debug(f"Extracting course info from room name: {room_name}")
    
    # Expected format: "course_<course_id>_<course_name>" or similar
    try:
        if "_" in room_name:
            parts = room_name.split("_")
            if len(parts) >= 3 and parts[0] == "course":
                course_id = parts[1]
                course_name = "_".join(parts[2:]).replace("_", " ")
                logger.info(f"Extracted course info - ID: {course_id}, Name: {course_name}")
                return course_id, course_name
    except Exception as e:
        logger.warning(f"Failed to extract course info from room name: {room_name}", exc_info=True)
    
    logger.info("Using default course info (no specific course)")
    return None, None


async def entrypoint(ctx: agents.JobContext):
    logger.info("Starting voice agent entrypoint")
    
    # Extract course information from room context
    room_name = ctx.room.name if ctx.room else "default_room"
    course_id, course_name = extract_course_info_from_room(room_name)
    
    # Store user session info
    user_id = getattr(ctx, 'participant_identity', 'anonymous')
    user_sessions[user_id] = {
        'course_id': course_id,
        'course_name': course_name,
        'room_name': room_name,
        'session_start_time': asyncio.get_event_loop().time()
    }
    
    logger.info(f"Starting teaching session - Room: {room_name}, Course: {course_name} (ID: {course_id}), User: {user_id}")
    
    # Load configuration
    config = load_voice_agent_config()
    connection_config = config['voice_agent']['connection']
    model_config = config['voice_agent']['model']
    greeting_config = config['voice_agent']['greeting']
    
    # Connection retry configuration
    max_retries = connection_config['max_retries']
    retry_delay = connection_config['retry_delay']
    
    session = None
    teacher = None
    
    for attempt in range(max_retries):
        try:
            # Create teacher assistant with course context
            teacher = TeacherAssistant(course_id=course_id, course_name=course_name)
            
            session = AgentSession(
                llm=google.beta.realtime.RealtimeModel(
                    model=model_config['name'],
                    voice=model_config['voice'],
                    temperature=model_config['temperature'],
                    instructions=teacher.instructions,
                ),
            )
            break  # Success, exit retry loop
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                logger.error("All connection attempts failed")
                raise

    # Flag to track if greeting has been sent (moved outside retry loop)
    greeting_sent = False

    async def send_greeting():
        """Send greeting message to the user"""
        nonlocal greeting_sent
        if greeting_sent or not session or not teacher:
            return
            
        try:
            greeting = teacher.get_greeting_message()
            logger.info(f"Sending greeting to user: {greeting}")
            
            await session.generate_reply(
                instructions=f"Say this greeting message: {greeting}"
            )
            
            greeting_sent = True
            logger.info("Greeting message sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send greeting: {e}")

    # Set up participant connection event handler
    def on_participant_connected(participant):
        """Handle when a participant connects to the room"""
        logger.info(f"Participant connected: {participant.identity}")
        # Only send greeting to human participants (not the agent itself)
        if participant.kind != ParticipantKind.AGENT:
            asyncio.create_task(send_greeting())

    # Register the event handler
    ctx.room.on("participant_connected", on_participant_connected)

    # Start the session
    await session.start(
        room=ctx.room,
        agent=teacher,
        room_input_options=RoomInputOptions(),
    )

    # Wait a moment for session to be fully established
    await asyncio.sleep(greeting_config['delay_seconds'])

    # Check if there are already participants in the room and send greeting
    for participant in ctx.room.remote_participants.values():
        if participant.kind != ParticipantKind.AGENT:
            logger.info(f"Found existing participant: {participant.identity}")
            await send_greeting()
            break

    # If no participants yet, wait a moment and try sending greeting anyway
    if not greeting_sent:
        await asyncio.sleep(greeting_config['fallback_delay_seconds'])
        await send_greeting()
    
    # Start periodic session cleanup
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    logger.info("Voice agent session started successfully")
    
    # Monitor session health
    try:
        await monitor_session_health(session, user_id)
    
    except Exception as e:
        logger.error(f"Session health monitoring error for user {user_id}: {e}")
        # Clean up user session on failure
        if user_id in user_sessions:
            del user_sessions[user_id]
        raise
    finally:
        cleanup_task.cancel()

async def periodic_cleanup():
    """Periodically clean up expired sessions"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await cleanup_expired_sessions()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")

async def monitor_session_health(session, user_id: str):
    """Monitor session health and handle disconnections"""
    try:
        # This would typically involve monitoring the session state
        # For now, we'll just wait for the session to end naturally
        await session.wait_for_completion()
    except Exception as e:
        logger.error(f"Session health monitoring error for user {user_id}: {e}")
    finally:
        # Clean up user session when monitoring ends
        if user_id in user_sessions:
            logger.info(f"Cleaning up session for user: {user_id}")
            del user_sessions[user_id]


if __name__ == "__main__":
    logger.info("Starting voice agent application")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except Exception as e:
        logger.exception("Voice agent application failed to start")
        raise