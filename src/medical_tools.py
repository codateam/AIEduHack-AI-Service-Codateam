from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import json
from pathlib import Path

from medical_models import (
    Patient, HealthcareProfessional, Appointment, AppointmentRequest,
    Prescription, PrescriptionRefillRequest, Subscription, Payment,
    TriageAssessment, UrgencyLevel, AppointmentType, AppointmentStatus,
    PrescriptionStatus, SubscriptionType, SubscriptionStatus, ToolCall
)
from utils.logger import logger

logger.info("MedicalTools initialized")


class MedicalDatabase:
    """Simple in-memory database for medical data (replace with real database in production)"""
    
    def __init__(self):
        self.patients: Dict[str, Patient] = {}
        self.professionals: Dict[str, HealthcareProfessional] = {}
        self.appointments: Dict[str, Appointment] = {}
        self.prescriptions: Dict[str, Prescription] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.payments: Dict[str, Payment] = {}
        self.triage_assessments: Dict[str, TriageAssessment] = {}
        self._load_sample_data()
    
    def _load_sample_data(self):
        """Load sample data for demonstration"""
        # Sample healthcare professionals
        self.professionals["doc_001"] = HealthcareProfessional(
            id="doc_001",
            first_name="Dr. Sarah",
            last_name="Johnson",
            email="sarah.johnson@hospital.com",
            phone="555-0101",
            specialization="General Medicine",
            license_number="MD12345",
            department="General Practice",
            consultation_fee=150.0
        )
        
        self.professionals["doc_002"] = HealthcareProfessional(
            id="doc_002",
            first_name="Dr. Michael",
            last_name="Chen",
            email="michael.chen@hospital.com",
            phone="555-0102",
            specialization="Cardiology",
            license_number="MD12346",
            department="Cardiology",
            consultation_fee=250.0
        )
        
        self.professionals["doc_003"] = HealthcareProfessional(
            id="doc_003",
            first_name="Dr. Emily",
            last_name="Rodriguez",
            email="emily.rodriguez@hospital.com",
            phone="555-0103",
            specialization="Dermatology",
            license_number="MD12347",
            department="Dermatology",
            consultation_fee=200.0
        )

# Global database instance
medical_db = MedicalDatabase()

class TriageTools:
    """Tools for the Triage Agent"""
    
    @staticmethod
    def assess_urgency(symptoms: List[str], additional_info: str = "") -> ToolCall:
        """Assess the urgency level based on symptoms"""
        try:
            # Emergency keywords
            emergency_keywords = [
                "chest pain", "difficulty breathing", "severe bleeding", "unconscious",
                "heart attack", "stroke", "severe allergic reaction", "poisoning"
            ]
            
            # High urgency keywords
            high_urgency_keywords = [
                "severe pain", "high fever", "vomiting blood", "severe headache",
                "broken bone", "deep cut", "severe burn"
            ]
            
            # Medium urgency keywords
            medium_urgency_keywords = [
                "fever", "persistent cough", "moderate pain", "rash", "nausea"
            ]
            
            symptoms_text = " ".join(symptoms).lower() + " " + additional_info.lower()
            
            urgency = UrgencyLevel.LOW
            recommended_action = "Schedule a routine appointment"
            
            if any(keyword in symptoms_text for keyword in emergency_keywords):
                urgency = UrgencyLevel.EMERGENCY
                recommended_action = "Seek immediate emergency care - call 911"
            elif any(keyword in symptoms_text for keyword in high_urgency_keywords):
                urgency = UrgencyLevel.HIGH
                recommended_action = "Schedule urgent care appointment within 24 hours"
            elif any(keyword in symptoms_text for keyword in medium_urgency_keywords):
                urgency = UrgencyLevel.MEDIUM
                recommended_action = "Schedule appointment within 2-3 days"
            
            result = {
                "urgency_level": urgency,
                "recommended_action": recommended_action,
                "assessment_reasoning": f"Based on symptoms: {', '.join(symptoms)}"
            }
            
            return ToolCall(
                tool_name="assess_urgency",
                parameters={"symptoms": symptoms, "additional_info": additional_info},
                result=result,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in assess_urgency: {e}")
            return ToolCall(
                tool_name="assess_urgency",
                parameters={"symptoms": symptoms, "additional_info": additional_info},
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def recommend_department(symptoms: List[str], urgency: UrgencyLevel) -> ToolCall:
        """Recommend appropriate department based on symptoms"""
        try:
            department_mapping = {
                "cardiology": ["chest pain", "heart", "cardiac", "palpitations", "blood pressure"],
                "dermatology": ["rash", "skin", "acne", "mole", "eczema", "psoriasis"],
                "orthopedics": ["bone", "joint", "fracture", "sprain", "back pain", "knee pain"],
                "neurology": ["headache", "migraine", "seizure", "numbness", "dizziness"],
                "gastroenterology": ["stomach", "nausea", "vomiting", "diarrhea", "constipation"],
                "general practice": ["fever", "cold", "flu", "general checkup", "routine"]
            }
            
            symptoms_text = " ".join(symptoms).lower()
            recommended_dept = "general practice"  # default
            
            for dept, keywords in department_mapping.items():
                if any(keyword in symptoms_text for keyword in keywords):
                    recommended_dept = dept
                    break
            
            # Override for emergency cases
            if urgency == UrgencyLevel.EMERGENCY:
                recommended_dept = "emergency"
            
            result = {
                "recommended_department": recommended_dept,
                "reasoning": f"Based on symptoms indicating {recommended_dept} specialty"
            }
            
            return ToolCall(
                tool_name="recommend_department",
                parameters={"symptoms": symptoms, "urgency": urgency.value},
                result=result,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in recommend_department: {e}")
            return ToolCall(
                tool_name="recommend_department",
                parameters={"symptoms": symptoms, "urgency": urgency.value},
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def create_triage_assessment(patient_id: str, symptoms: List[str], additional_info: str = "") -> ToolCall:
        """Create a complete triage assessment"""
        try:
            urgency_result = TriageTools.assess_urgency(symptoms, additional_info)
            if not urgency_result.success:
                return urgency_result
            
            urgency_level = UrgencyLevel(urgency_result.result["urgency_level"])
            dept_result = TriageTools.recommend_department(symptoms, urgency_level)
            
            assessment = TriageAssessment(
                patient_id=patient_id,
                symptoms=symptoms,
                urgency_level=urgency_level,
                recommended_action=urgency_result.result["recommended_action"],
                recommended_department=dept_result.result["recommended_department"] if dept_result.success else None,
                notes=additional_info
            )
            
            medical_db.triage_assessments[assessment.assessment_id] = assessment
            
            return ToolCall(
                tool_name="create_triage_assessment",
                parameters={"patient_id": patient_id, "symptoms": symptoms, "additional_info": additional_info},
                result=assessment.model_dump(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in create_triage_assessment: {e}")
            return ToolCall(
                tool_name="create_triage_assessment",
                parameters={"patient_id": patient_id, "symptoms": symptoms, "additional_info": additional_info},
                success=False,
                error_message=str(e)
            )

class SupportTools:
    """Tools for the Support Agent"""
    
    @staticmethod
    def find_available_professionals(department: str, date_requested: date = None) -> ToolCall:
        """Find available healthcare professionals in a department"""
        try:
            if date_requested is None:
                date_requested = date.today()
            
            available_professionals = [
                prof for prof in medical_db.professionals.values()
                if department.lower() in prof.department.lower() or department.lower() == "general practice"
            ]
            
            result = [
                {
                    "id": prof.id,
                    "name": f"{prof.first_name} {prof.last_name}",
                    "specialization": prof.specialization,
                    "department": prof.department,
                    "consultation_fee": prof.consultation_fee
                }
                for prof in available_professionals
            ]
            
            return ToolCall(
                tool_name="find_available_professionals",
                parameters={"department": department, "date_requested": date_requested.isoformat()},
                result=result,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in find_available_professionals: {e}")
            return ToolCall(
                tool_name="find_available_professionals",
                parameters={"department": department, "date_requested": date_requested.isoformat() if date_requested else None},
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def schedule_appointment(appointment_request: AppointmentRequest) -> ToolCall:
        """Schedule an appointment"""
        try:
            # Find available doctor if not specified
            if not appointment_request.doctor_id:
                professionals_result = SupportTools.find_available_professionals(
                    appointment_request.department or "general practice",
                    appointment_request.preferred_date
                )
                if professionals_result.success and professionals_result.result:
                    appointment_request.doctor_id = professionals_result.result[0]["id"]
                else:
                    return ToolCall(
                        tool_name="schedule_appointment",
                        parameters=appointment_request.model_dump(),
                        success=False,
                        error_message="No available professionals found"
                    )
            
            # Create appointment
            appointment_datetime = datetime.combine(
                appointment_request.preferred_date,
                appointment_request.preferred_time or datetime.now().time().replace(hour=9, minute=0)
            )
            
            appointment = Appointment(
                patient_id=appointment_request.patient_id,
                doctor_id=appointment_request.doctor_id,
                appointment_date=appointment_datetime,
                appointment_type=appointment_request.appointment_type,
                department=appointment_request.department or "general practice",
                reason=appointment_request.reason,
                notes=appointment_request.notes
            )
            
            medical_db.appointments[appointment.appointment_id] = appointment
            
            return ToolCall(
                tool_name="schedule_appointment",
                parameters=appointment_request.model_dump(),
                result=appointment.model_dump(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in schedule_appointment: {e}")
            return ToolCall(
                tool_name="schedule_appointment",
                parameters=appointment_request.model_dump(),
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def process_prescription_refill(refill_request: PrescriptionRefillRequest) -> ToolCall:
        """Process a prescription refill request"""
        try:
            # Find existing prescription
            existing_prescription = None
            if refill_request.current_prescription_id:
                existing_prescription = medical_db.prescriptions.get(refill_request.current_prescription_id)
            
            if not existing_prescription:
                # Search by patient and medication
                for prescription in medical_db.prescriptions.values():
                    if (prescription.patient_id == refill_request.patient_id and 
                        prescription.medication_name.lower() == refill_request.medication_name.lower()):
                        existing_prescription = prescription
                        break
            
            if existing_prescription and existing_prescription.refills_remaining > 0:
                # Process refill
                existing_prescription.refills_remaining -= 1
                existing_prescription.status = PrescriptionStatus.READY
                if refill_request.pharmacy_preference:
                    existing_prescription.pharmacy = refill_request.pharmacy_preference
                
                result = {
                    "prescription_id": existing_prescription.prescription_id,
                    "status": "approved",
                    "refills_remaining": existing_prescription.refills_remaining,
                    "pharmacy": existing_prescription.pharmacy,
                    "message": "Prescription refill approved and ready for pickup"
                }
            else:
                result = {
                    "status": "requires_approval",
                    "message": "Prescription refill requires doctor approval. Please schedule an appointment."
                }
            
            return ToolCall(
                tool_name="process_prescription_refill",
                parameters=refill_request.model_dump(),
                result=result,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in process_prescription_refill: {e}")
            return ToolCall(
                tool_name="process_prescription_refill",
                parameters=refill_request.model_dump(),
                success=False,
                error_message=str(e)
            )

class BillingTools:
    """Tools for the Billing Agent"""
    
    @staticmethod
    def get_subscription_info(user_id: str) -> ToolCall:
        """Get subscription information for a user"""
        try:
            user_subscriptions = [
                sub for sub in medical_db.subscriptions.values()
                if sub.user_id == user_id
            ]
            
            if user_subscriptions:
                # Get the most recent active subscription
                active_subscription = max(
                    [sub for sub in user_subscriptions if sub.status == SubscriptionStatus.ACTIVE],
                    key=lambda x: x.start_date,
                    default=None
                )
                
                if active_subscription:
                    result = active_subscription.model_dump()
                else:
                    result = {"status": "no_active_subscription", "message": "No active subscription found"}
            else:
                result = {"status": "no_subscription", "message": "No subscription found for this user"}
            
            return ToolCall(
                tool_name="get_subscription_info",
                parameters={"user_id": user_id},
                result=result,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in get_subscription_info: {e}")
            return ToolCall(
                tool_name="get_subscription_info",
                parameters={"user_id": user_id},
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def update_subscription(user_id: str, subscription_type: SubscriptionType) -> ToolCall:
        """Update or create a subscription"""
        try:
            # Check for existing subscription
            existing_subscription = None
            for sub in medical_db.subscriptions.values():
                if sub.user_id == user_id and sub.status == SubscriptionStatus.ACTIVE:
                    existing_subscription = sub
                    break
            
            subscription_fees = {
                SubscriptionType.BASIC: 29.99,
                SubscriptionType.PREMIUM: 59.99,
                SubscriptionType.FAMILY: 89.99,
                SubscriptionType.CORPORATE: 199.99
            }
            
            subscription_features = {
                SubscriptionType.BASIC: ["Basic consultations", "Prescription refills"],
                SubscriptionType.PREMIUM: ["All basic features", "Priority scheduling", "Telemedicine"],
                SubscriptionType.FAMILY: ["All premium features", "Family member coverage", "Health tracking"],
                SubscriptionType.CORPORATE: ["All family features", "Corporate wellness", "Bulk billing"]
            }
            
            if existing_subscription:
                # Update existing subscription
                existing_subscription.subscription_type = subscription_type
                existing_subscription.monthly_fee = subscription_fees[subscription_type]
                existing_subscription.features = subscription_features[subscription_type]
                result = existing_subscription.model_dump()
                result["action"] = "updated"
            else:
                # Create new subscription
                new_subscription = Subscription(
                    user_id=user_id,
                    subscription_type=subscription_type,
                    start_date=date.today(),
                    monthly_fee=subscription_fees[subscription_type],
                    features=subscription_features[subscription_type]
                )
                medical_db.subscriptions[new_subscription.subscription_id] = new_subscription
                result = new_subscription.model_dump()
                result["action"] = "created"
            
            return ToolCall(
                tool_name="update_subscription",
                parameters={"user_id": user_id, "subscription_type": subscription_type.value},
                result=result,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in update_subscription: {e}")
            return ToolCall(
                tool_name="update_subscription",
                parameters={"user_id": user_id, "subscription_type": subscription_type.value},
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def process_payment(user_id: str, amount: float, payment_method: str, description: str = "") -> ToolCall:
        """Process a payment"""
        try:
            payment = Payment(
                user_id=user_id,
                amount=amount,
                payment_method=payment_method,
                description=description
            )
            
            # Simulate payment processing
            # In real implementation, this would integrate with payment gateway
            payment.status = "paid"  # Assuming successful payment
            
            medical_db.payments[payment.payment_id] = payment
            
            result = payment.model_dump()
            result["message"] = "Payment processed successfully"
            
            return ToolCall(
                tool_name="process_payment",
                parameters={"user_id": user_id, "amount": amount, "payment_method": payment_method, "description": description},
                result=result,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in process_payment: {e}")
            return ToolCall(
                tool_name="process_payment",
                parameters={"user_id": user_id, "amount": amount, "payment_method": payment_method, "description": description},
                success=False,
                error_message=str(e)
            )