import sys
import os
import yaml
from typing import Dict, Any, Optional, List

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google

from medical_agents import TriageAgent, SupportAgent, BillingAgent
from session_manager import session_manager
from medical_models import Patient, UrgencyLevel
from utils.logger import logger

load_dotenv()

# Initialize logger
logger.info("MedicalConsultationAgent initialized")

# # Medical Assistance
# class Medi
