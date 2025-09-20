# Specialty Determination Agent

## Overview

The SpecialtyDeterminationAgent has been added to the medical assistance workflow to help patients who don't know which medical specialty they need. This agent analyzes symptoms and recommends the most appropriate specialist.

## Agent Flow

The updated workflow now includes:

1. **ConsentCollectorAgent** - Collects recording consent
2. **IntakeAgent** - Collects basic patient information
3. **TriageAgent** - Assesses urgency and medical history
4. **SpecialtyDeterminationAgent** - ⭐ NEW: Determines appropriate specialty
5. **CareCoordinatorAgent** - Schedules appointments with specialty information
6. **EmergencyAgent** - Handles emergency situations (bypasses specialty determination)

## Specialty Determination Features

### Available Specialties

- **Cardiology** - Heart and cardiovascular system
- **Dermatology** - Skin, hair, and nail conditions
- **Orthopedics** - Bones, joints, and musculoskeletal system
- **Neurology** - Brain, spinal cord, and nervous system
- **Gastroenterology** - Digestive system and stomach issues
- **Pulmonology** - Lungs and respiratory system
- **Endocrinology** - Hormones and metabolic disorders
- **Psychiatry** - Mental health and behavioral disorders
- **Ophthalmology** - Eyes and vision
- **ENT** - Ear, nose, throat, and head/neck issues
- **Urology** - Urinary system and male reproductive health
- **Gynecology** - Women's reproductive health
- **General Medicine** - General health concerns and preventive care

### Agent Capabilities

- **Symptom Analysis**: Analyzes patient symptoms against specialty keywords
- **Clarifying Questions**: Asks targeted questions to better understand conditions
- **Confidence Assessment**: Provides high/medium/low confidence ratings
- **Multiple Specialties**: Can recommend multiple specialists when appropriate
- **Reasoning**: Explains recommendations clearly to patients

### Configuration

Specialty prompts and configurations are stored in:
`src/configs/specialty_prompts.yaml`

This YAML file contains:

- Specialty definitions and descriptions
- Assessment questions
- Response templates
- Keyword mappings

### Data Storage

The `MedicalSessionInfo` dataclass now includes:

- `recommended_specialty`: The recommended specialty
- `specialty_confidence`: Confidence level (high/medium/low)

### Integration

- Non-emergency cases flow through specialty determination
- Emergency cases bypass specialty determination and go directly to EmergencyAgent
- Care coordinator receives specialty information for appointment scheduling
- Appointment scheduling includes specialty details

## Usage

The agent automatically activates after triage assessment for non-emergency cases. It will:

1. Greet the patient and explain its purpose
2. Ask clarifying questions if needed
3. Analyze symptoms and recommend appropriate specialty
4. Hand off to care coordinator with specialty information

## Benefits

- Reduces patient confusion about which specialist to see
- Improves appointment accuracy and efficiency
- Provides educational value about medical specialties
- Maintains professional medical consultation flow
- Supports both single and multiple specialty recommendations
