"""
slm_engine.py

Core SLM Decision Making Engine for HealthOS.

Replaces conditional keyword-based heuristics with Small Language Model (SLM)
inference for:
1. Intent Classification (Emergency vs Booking vs Triage)
2. Medical Entity Extraction (symptoms, doctor_name, department, date, time_slot, patient_name)
3. Symptom-to-Department Classification with Ambiguity Detection
4. User Indecision Detection (routing to General Medicine when user cannot decide)

Designed to work with local GGUF models (e.g. BioMedLM-7B, TinyLlama) via llama_cpp.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple


class SLMEngine:
    """
    SLM Inference and Decision Engine.
    Handles all semantic decisions without relying on hardcoded keyword rules.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        slm_instance=None,
        n_ctx: int = 2048,
        n_threads: int = 8,
    ):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = config_path or os.path.join(self.base_dir, "config.json")
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.slm = slm_instance

        if self.slm is None and (self.model_path or os.path.exists(self.config_path)):
            self._init_slm()

    def _init_slm(self):
        """Loads the local SLM via llama_cpp if model file exists."""
        if not self.model_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                bio_cfg = cfg.get("BioMedLM_CONFIG", {})
                rel_path = bio_cfg.get("model_path", "")
                resolved = os.path.normpath(os.path.join(self.base_dir, "agents", rel_path))
                if os.path.exists(resolved):
                    self.model_path = resolved
                else:
                    alt_path = os.path.join(self.base_dir, "models", "BioMedLM-7B.Q4_K_M.gguf")
                    if os.path.exists(alt_path):
                        self.model_path = alt_path
            except Exception:
                pass

        if self.model_path and os.path.exists(self.model_path):
            try:
                import llama_cpp
                self.slm = llama_cpp.Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    verbose=False,
                )
            except Exception as e:
                print(f"[SLMEngine] Warning: Could not initialize llama_cpp: {e}")
                self.slm = None

    def is_available(self) -> bool:
        """Returns True if the SLM model is loaded in memory."""
        return self.slm is not None

    def query_json(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 300) -> Dict[str, Any]:
        """Runs inference and parses the response strictly as a JSON object."""
        if not self.is_available():
            return {}

        sys_msg = system_prompt or (
            "You are HealthOS SLM Decision Engine. You analyze patient messages. "
            "Always respond with a strictly valid JSON object without markdown formatting, "
            "code blocks, or explanations."
        )

        try:
            res = self.slm.create_chat_completion(
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            raw = res["choices"][0]["message"]["content"].strip()
            return self._parse_json_safe(raw)
        except Exception as e:
            print(f"[SLMEngine] Error during SLM query: {e}")
            return {}

    def _parse_json_safe(self, text: str) -> Dict[str, Any]:
        """Extracts and parses JSON from SLM text output."""
        if not text:
            return {}

        # Strip markdown ```json code fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()

        # Try direct parse
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Try finding outer JSON curly braces
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        return {}

    # =========================================================================
    # 1. SLM INTENT & ENTITY EXTRACTION (NO KEYWORD CHECKS)
    # =========================================================================

    def classify_intent_and_entities(
        self,
        user_message: str,
        available_departments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Uses SLM to classify intent and extract entities from the user message.
        Replaces all conditional string/regex checks.
        """
        if not self.is_available():
            return self._fallback_extraction(user_message, available_departments)

        dept_str = ", ".join(available_departments) if available_departments else "Cardiology, Dermatology, General Medicine, Orthopedics, Neurology, Pulmonology"

        system_prompt = (
            "You are HealthOS Clinical Intent and Entity Extraction Engine. "
            "Analyze the patient message and output strictly valid JSON. "
            "Do not include explanations, preambles, or markdown formatting.\n\n"
            f"Available hospital departments: [{dept_str}]\n\n"
            "Classification Rules:\n"
            "1. intent:\n"
            "   - 'emergency': ONLY for acute, life-threatening symptoms (e.g. crushing chest pain, difficulty breathing, stroke, unconsciousness, heavy bleeding).\n"
            "   - 'booking': Patient wants to consult, see, visit, or book a doctor or specialist (e.g. 'I want to see a cardiologist', 'book an appointment', 'visit Dr. Sharma'). Never classify as emergency.\n"
            "   - 'triage': Patient reports non-emergency symptoms, discomfort, or medical issues for evaluation (e.g. 'rash on arm', 'fever and cough').\n"
            "2. Entities:\n"
            "   - 'symptoms': list of physical symptoms mentioned, or [].\n"
            "   - 'doctor_name': exact doctor name if mentioned, or null.\n"
            "   - 'department': department name if mentioned or implied by specialist (e.g. cardiologist -> Cardiology), or null.\n"
            "   - 'date': requested date if mentioned, or null.\n"
            "   - 'time_slot': requested time if mentioned, or null.\n"
            "   - 'patient_name': patient name if stated, or null.\n"
            "   - 'is_undecided': true if user expresses indecision or uncertainty, or false.\n\n"
            "Few-Shot Exemplars:\n"
            "Example 1:\n"
            "User: \"I want to see a cardiologist for a checkup tomorrow\"\n"
            "JSON:\n"
            "{\"intent\": \"booking\", \"symptoms\": [], \"doctor_name\": null, \"department\": \"Cardiology\", \"date\": \"tomorrow\", \"time_slot\": null, \"patient_name\": null, \"is_undecided\": false}\n\n"
            "Example 2:\n"
            "User: \"I am having severe crushing chest pain and cannot breathe\"\n"
            "JSON:\n"
            "{\"intent\": \"emergency\", \"symptoms\": [\"severe crushing chest pain\", \"cannot breathe\"], \"doctor_name\": null, \"department\": \"Cardiology\", \"date\": null, \"time_slot\": null, \"patient_name\": null, \"is_undecided\": false}\n\n"
            "Example 3:\n"
            "User: \"I have had a red itchy rash on my arm for three days\"\n"
            "JSON:\n"
            "{\"intent\": \"triage\", \"symptoms\": [\"red itchy rash on arm\"], \"doctor_name\": null, \"department\": \"Dermatology\", \"date\": null, \"time_slot\": null, \"patient_name\": null, \"is_undecided\": false}"
        )

        user_prompt = (
            f"Analyze the user message:\n"
            f"User message: \"{user_message}\"\n"
            f"Respond with strictly valid JSON only:"
        )

        result = self.query_json(user_prompt, system_prompt=system_prompt, max_tokens=250)
        if not result or "intent" not in result:
            return self._fallback_extraction(user_message, available_departments)

        # Hallucination filter: Ensure doctor_name was actually mentioned in the user message
        doc = result.get("doctor_name")
        if doc and isinstance(doc, str):
            clean_tokens = [t.lower() for t in doc.replace("Dr.", "").replace("Dr", "").replace(".", "").split() if len(t) >= 3]
            if not any(t in user_message.lower() for t in clean_tokens):
                result["doctor_name"] = None

        return result

    # =========================================================================
    # 2. SLM DEPARTMENT CLASSIFICATION & AMBIGUITY DETECTION
    # =========================================================================

    def classify_department(
        self,
        symptoms: List[str],
        available_departments: List[str],
    ) -> Dict[str, Any]:
        """
        SLM classifies patient symptoms into an appropriate medical department.
        Detects ambiguity: if symptoms are vague, multi-system, or unclear,
        sets is_ambiguous=True and department=None.
        """
        if not symptoms:
            return {
                "department": None,
                "confidence": 0.0,
                "is_ambiguous": True,
                "reasoning": "No symptoms provided to classify.",
            }

        if not self.is_available():
            return self._fallback_department_classification(symptoms, available_departments)

        symptoms_str = ", ".join(symptoms) if isinstance(symptoms, list) else str(symptoms)
        dept_str = ", ".join(available_departments)

        system_prompt = (
            "You are an expert clinical triage SLM for hospital department routing. "
            "Analyze patient reported symptoms and determine the single most appropriate medical department. "
            "Respond with strictly valid JSON only.\n\n"
            f"Available hospital departments: [{dept_str}]\n\n"
            "Rules:\n"
            "- If symptoms clearly map to a single specialty (e.g. rash -> Dermatology, chest pain -> Cardiology, bone fracture -> Orthopedics), "
            "set 'department' to that exact department name and 'is_ambiguous': false.\n"
            "- If symptoms are vague, generalized, multi-system, or unclear (e.g. 'feel unwell', 'tired and weak with general aches'), "
            "set 'department': null and 'is_ambiguous': true.\n"
            "- 'confidence' must be a float between 0.0 and 1.0.\n\n"
            "Few-Shot Exemplars:\n"
            "Example 1:\n"
            "Symptoms: \"red itchy rash and dry patches on skin\"\n"
            "JSON:\n"
            "{\"department\": \"Dermatology\", \"confidence\": 0.95, \"is_ambiguous\": false, \"reasoning\": \"Classic dermatological presentation.\"}\n\n"
            "Example 2:\n"
            "Symptoms: \"I just feel generally unwell and tired with body aches\"\n"
            "JSON:\n"
            "{\"department\": null, \"confidence\": 0.40, \"is_ambiguous\": true, \"reasoning\": \"Vague non-specific multi-system symptoms.\"}"
        )

        user_prompt = (
            f"Task: Classify patient symptoms using expert clinical triage SLM rules.\n"
            f"Patient reported symptoms: \"{symptoms_str}\"\n"
            f"Respond with strictly valid JSON only:"
        )

        result = self.query_json(user_prompt, system_prompt=system_prompt, max_tokens=200)

        # Validate department against available list
        dept = result.get("department")
        is_ambiguous = result.get("is_ambiguous", False)

        if dept:
            # Case-insensitive match with available departments
            matched = next((d for d in available_departments if d.lower() == str(dept).strip().lower()), None)
            if matched:
                result["department"] = matched
            else:
                # Ambiguous or invalid department returned by SLM
                result["department"] = None
                result["is_ambiguous"] = True

        if not result.get("department") or is_ambiguous:
            result["is_ambiguous"] = True
            result["department"] = None

        return result

    # =========================================================================
    # 3. USER INDECISION DETECTION (FALLBACK TO GENERAL MEDICINE)
    # =========================================================================

    def is_user_undecided(self, user_message: str) -> bool:
        """
        Uses SLM to determine if the user is expressing indecision or inability
        to choose a department (e.g. "I don't know", "not sure", "you decide").
        """
        if not user_message:
            return True

        if not self.is_available():
            return self._fallback_is_undecided(user_message)

        system_prompt = (
            "You are HealthOS Clinical Indecision Classifier. "
            "The patient was asked to choose a medical department or specialist. "
            "Determine whether the user is unable to decide, expresses uncertainty, or asks the system/doctor to choose. "
            "Respond with strictly valid JSON only.\n\n"
            "Few-Shot Exemplars:\n"
            "Example 1:\n"
            "User: \"I don't know, you decide for me\"\n"
            "JSON:\n"
            "{\"is_undecided\": true, \"chosen_department\": null}\n\n"
            "Example 2:\n"
            "User: \"Cardiology please\"\n"
            "JSON:\n"
            "{\"is_undecided\": false, \"chosen_department\": \"Cardiology\"}\n\n"
            "Example 3:\n"
            "User: \"Not sure what department, whatever is best\"\n"
            "JSON:\n"
            "{\"is_undecided\": true, \"chosen_department\": null}"
        )

        user_prompt = (
            f"Determine whether the user is unable to decide:\n"
            f"User response: \"{user_message}\"\n"
            f"Respond with strictly valid JSON only:"
        )

        result = self.query_json(user_prompt, system_prompt=system_prompt, max_tokens=100)
        return bool(result.get("is_undecided", False))

    # =========================================================================
    # FALLBACKS (ONLY WHEN SLM BINARY NOT LOADED / RUNNING IN LIGHTWEIGHT TESTS)
    # =========================================================================

    def _fallback_extraction(self, user_message: str, departments: Optional[List[str]]) -> Dict[str, Any]:
        """Safe fallback structure for tests where SLM is not instantiated."""
        res: Dict[str, Any] = {
            "intent": "triage",
            "symptoms": [],
            "doctor_name": None,
            "department": None,
            "date": None,
            "time_slot": None,
            "patient_name": None,
            "is_undecided": False,
        }
        low = user_message.lower()
        if any(w in low for w in ["emergency", "chest pain", "cannot breathe", "unconscious", "heart attack"]):
            res["intent"] = "emergency"
            res["symptoms"] = [user_message]
        elif any(w in low for w in ["book", "appointment", "schedule", "reserve"]):
            res["intent"] = "booking"
        elif any(w in low for w in ["don't know", "not sure", "cant decide", "can't decide", "no idea", "you choose"]):
            res["is_undecided"] = True

        if departments:
            for d in departments:
                if d.lower() in low:
                    res["department"] = d
                    break

        return res

    def _fallback_department_classification(self, symptoms: List[str], departments: List[str]) -> Dict[str, Any]:
        """Fallback for unit tests without SLM weights loaded."""
        text = " ".join(symptoms).lower() if isinstance(symptoms, list) else str(symptoms).lower()
        if any(w in text for w in ["chest", "heart", "cardio"]):
            return {"department": "Cardiology", "confidence": 0.92, "is_ambiguous": False, "reasoning": "Cardiovascular symptoms."}
        if any(w in text for w in ["skin", "rash", "itch"]):
            return {"department": "Dermatology", "confidence": 0.95, "is_ambiguous": False, "reasoning": "Dermatological symptoms."}
        if any(w in text for w in ["joint", "knee", "bone"]):
            return {"department": "Orthopedics", "confidence": 0.90, "is_ambiguous": False, "reasoning": "Orthopedic complaints."}

        # If general/vague, flag ambiguous
        return {"department": None, "confidence": 0.50, "is_ambiguous": True, "reasoning": "Vague or multi-system symptoms."}

    def _fallback_is_undecided(self, message: str) -> bool:
        low = message.lower()
        return any(p in low for p in ["not sure", "don't know", "dont know", "no idea", "can't decide", "you decide", "help me choose"])
