# Medical Office Triage Agent System

A modular voice agent system for medical office triage with three specialized agents: Triage Agent, Support Agent, and Billing Agent.

## 🏗️ System Architecture

### Core Components

1. **BaseModel & Data Models** (`src/models/medical_models.py`)
   - Comprehensive Pydantic models for all medical data
   - User session management with conversation history
   - Type-safe data structures for patients, appointments, prescriptions, etc.

2. **Session Manager** (`src/services/session_manager.py`)
   - Persistent session storage with JSON backend
   - Conversation history tracking
   - Context management across agent transfers

3. **Specialized Agents** (`src/agents/medical_agents.py`)
   - **Triage Agent**: Initial assessment and patient routing
   - **Support Agent**: Appointments, prescriptions, professional recommendations
   - **Billing Agent**: Subscription management and payment processing

4. **Tool System** (`src/tools/medical_tools.py`)
   - Modular tools for each agent type
   - In-memory database simulation
   - Comprehensive medical operations

5. **Main Orchestrator** (`src/medical_consultation_agent.py`)
   - Coordinates all three agents
   - Handles voice interactions via LiveKit
   - Manages agent transfers based on patient needs

## 🚀 Key Features

### Modular Design
- **Separation of Concerns**: Each agent handles specific medical office functions
- **Easy Extension**: Add new agents or tools without affecting existing functionality
- **Configuration-Driven**: YAML-based prompts and agent configurations

### Session Management
- **Persistent Sessions**: User data and conversation history saved across interactions
- **Context Preservation**: Maintains context during agent transfers
- **User Identification**: Extracts user info from room names

### Tool Calling System
- **Triage Tools**: Symptom assessment, urgency determination, department routing
- **Support Tools**: Professional recommendations, appointment scheduling, prescription refills
- **Billing Tools**: Subscription management, payment processing, billing inquiries

### Voice Integration
- **LiveKit Integration**: Real-time voice communication
- **Google Gemini**: Advanced language model for natural conversations
- **Dynamic Routing**: Automatic agent switching based on conversation content

## 📁 Project Structure

```
src/
├── models/
│   └── medical_models.py          # Pydantic models for all data structures
├── services/
│   └── session_manager.py         # Session management and persistence
├── agents/
│   └── medical_agents.py          # Three specialized medical agents
├── tools/
│   └── medical_tools.py           # Tool implementations for each agent
├── configs/
│   ├── medical_agents.yaml        # Agent configurations
│   └── medical_prompts.yaml       # Conversation prompts and flows
└── medical_consultation_agent.py  # Main orchestrator
```

## 🔧 Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   ```bash
   # Create .env file with your API keys
   GOOGLE_API_KEY=your_google_api_key
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   ```

3. **Run Tests**:
   ```bash
   python test_medical_agent.py
   ```

4. **Start Voice Agent**:
   ```bash
   python src/medical_consultation_agent.py
   ```

## 🎯 Usage Examples

### Patient Interaction Flow

1. **Initial Contact** (Triage Agent):
   ```
   Patient: "I have a severe headache and feel dizzy"
   Agent: "I understand you're experiencing a headache and dizziness. Let me assess your symptoms..."
   ```

2. **Appointment Scheduling** (Support Agent):
   ```
   Patient: "I need to schedule an appointment"
   Agent: "I'll help you schedule an appointment. What type of consultation do you need?"
   ```

3. **Billing Inquiry** (Billing Agent):
   ```
   Patient: "What's my current subscription status?"
   Agent: "Let me check your subscription details..."
   ```

### Agent Transfer Examples

- **Emergency Detection**: Automatically routes to emergency protocols
- **Keyword-Based Routing**: "billing", "appointment", "prescription" trigger agent switches
- **Context Preservation**: Previous conversation history maintained across transfers

## 🛠️ Customization

### Adding New Agents

1. Create agent class in `src/agents/medical_agents.py`
2. Add configuration in `src/configs/medical_agents.yaml`
3. Define prompts in `src/configs/medical_prompts.yaml`
4. Update main orchestrator routing logic

### Adding New Tools

1. Create tool class in `src/tools/medical_tools.py`
2. Implement required methods with proper return types
3. Integrate with appropriate agent class

### Modifying Conversation Flow

1. Update prompts in `src/configs/medical_prompts.yaml`
2. Adjust routing keywords in main orchestrator
3. Test with various patient scenarios

## 📊 Data Models

### Core Models
- **BaseUser**: Foundation for all user types
- **Patient**: Extended user with medical information
- **UserSession**: Session management with conversation history
- **TriageAssessment**: Medical triage results
- **Appointment**: Appointment scheduling data
- **Prescription**: Medication and refill information
- **Subscription**: Billing and subscription details

### Response Models
- **AgentResponse**: Base response structure
- **TriageResponse**: Triage-specific responses with urgency levels
- **SupportResponse**: Support agent responses with action confirmations
- **BillingResponse**: Billing agent responses with transaction details

## 🔒 Security Considerations

- **Data Validation**: All inputs validated through Pydantic models
- **Session Security**: Session IDs generated securely
- **Error Handling**: Comprehensive error handling with logging
- **Privacy**: No sensitive data logged or exposed

## 🧪 Testing

The system includes comprehensive tests covering:
- Session management functionality
- Agent initialization and transfers
- Patient input processing
- Tool calling operations
- Error handling scenarios

Run the test suite:
```bash
python test_medical_agent.py
```

## 🚀 Deployment

### Local Development
```bash
python src/medical_consultation_agent.py
```

### Production Deployment
1. Configure environment variables
2. Set up LiveKit server
3. Deploy with proper logging and monitoring
4. Configure load balancing for multiple agents

## 📈 Future Enhancements

- **NLP Integration**: Advanced symptom extraction and medical entity recognition
- **Database Integration**: Replace in-memory storage with persistent database
- **Multi-language Support**: Internationalization for global deployment
- **Analytics Dashboard**: Real-time monitoring and analytics
- **Integration APIs**: Connect with existing medical systems (EMR, billing systems)
- **Voice Biometrics**: Patient identification through voice patterns
- **Appointment Reminders**: Automated reminder system
- **Prescription Tracking**: Integration with pharmacy systems

## 📞 Support

For technical support or questions about the Medical Office Triage Agent System, please refer to the documentation or contact the development team.

---

**Note**: This system is designed for demonstration purposes. For production medical use, ensure compliance with HIPAA, medical regulations, and proper security measures.