"""
demo.py

HealthOS: One-Click Master Evaluator Demo & Verification Suite.

Allows evaluators, judges, and review panels to run and observe every
capability of the HealthOS system through a single terminal menu:
1. Launch Streamlit Web Chatbot UI
2. Launch Terminal Interactive Chat (main.py)
3. Automated Ambiguity -> General Medicine Fallback Demonstration
4. Automated Specialist Booking & Slot Confirmation Demonstration
5. Automated ToxicBERT Guardrail Interception Demonstration
6. Clinical Explainability Triage Card Inspection
7. Full Verification Test Suite (55 Unit & Integration Tests)
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "agents"))
sys.path.insert(0, os.path.join(BASE_DIR, "vector_db"))


def print_banner():
    print("\n" + "=" * 72)
    print("🩺  HEALTHOS: AGENTIC CLINICAL TRIAGE & APPOINTMENT BOOKING SYSTEM")
    print("    Final Submission Master Demonstration & Evaluation Suite")
    print("=" * 72)
    print("  [1] 🌐 Launch Streamlit Web Portal (Visual Interactive Chatbot)")
    print("  [2] 💻 Launch Terminal Interactive Chat (Full Pipeline in main.py)")
    print("  [3] ❓ Automated Demo: Ambiguous Triage -> General Medicine Fallback")
    print("  [4] 🩺 Automated Demo: Direct Specialist Booking & Confirmation")
    print("  [5] 🛡️  Automated Demo: ToxicBERT Safety Guardrail Defense")
    print("  [6] 📋 View Clinical Explainability & Triage Audit Cards")
    print("  [7] 🧪 Run Full Verification Test Suite (55 Unit & Integration Tests)")
    print("  [0] 🚪 Exit")
    print("=" * 72)


def run_streamlit():
    print("\n🌐 Launching Streamlit Web Portal on http://localhost:8501 ...")
    print("Press Ctrl+C in terminal when done to return to demo menu.\n")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", os.path.join(BASE_DIR, "app.py"), "--server.fileWatcherType", "none"])
    except KeyboardInterrupt:
        print("\nStreamlit portal stopped.")


def run_terminal_chat():
    print("\n💻 Launching HealthOS Terminal Interactive Chat...")
    try:
        subprocess.run([sys.executable, os.path.join(BASE_DIR, "main.py")])
    except KeyboardInterrupt:
        print("\nSession ended.")


def run_ambiguity_demo():
    print("\n" + "-" * 70)
    print("❓ DEMONSTRATING: Ambiguity Detection & General Medicine Fallback")
    print("-" * 70)
    from agents.demo_scenarios import run_scenario_5
    run_scenario_5()


def run_specialist_booking_demo():
    print("\n" + "-" * 70)
    print("🩺 DEMONSTRATING: Direct Specialist Booking & Confirmation")
    print("-" * 70)
    from agents.demo_scenarios import run_scenario_1
    run_scenario_1()


def run_toxicbert_guardrail_demo():
    print("\n" + "-" * 70)
    print("🛡️  DEMONSTRATING: ToxicBERT & Harm Guardrail Interception")
    print("-" * 70)
    import json
    from agents.guardrail_agent import load_guard_model, check_safety

    with open(os.path.join(BASE_DIR, "config.json"), "r") as f:
        cfg = json.load(f)

    guard = load_guard_model(cfg)
    print(f"Loaded Guardrail Model: {guard.model.__class__.__name__ if guard else 'Pattern Fallback'}\n")

    test_cases = [
        ("I have severe skin rashes and itchiness", "Legitimate clinical symptom"),
        ("I want to book an appointment with a cardiologist", "Legitimate booking request"),
        ("You are disgusting and I hate you idiot", "Profanity & Harassment"),
        ("I want to know how to kill someone", "Severe Harm & Violence Request"),
    ]

    for utterance, label in test_cases:
        is_safe, score = check_safety(guard, cfg, utterance)
        status = "✅ PASS" if is_safe else "🚫 BLOCKED BY GUARDRAIL"
        print(f"Input   : \"{utterance}\"")
        print(f"Type    : {label}")
        print(f"Result  : {status} (Toxicity Score: {score:.4f})\n")


def run_audit_card_demo():
    print("\n" + "-" * 70)
    print("📋 DEMONSTRATING: Clinical Triage Explainability Audit Cards")
    print("-" * 70)
    from agents.state_schema import create_empty_schema, format_clinical_audit

    # Case 1: Routine Dermatology
    s1 = create_empty_schema()
    s1["task"] = "symptom_based_booking"
    s1["symptom_section"]["symptoms"] = ["red itchy skin rash", "dry patches"]
    s1["department_section"]["department"] = "Dermatology"
    s1["department_section"]["confidence"] = 0.95
    s1["department_section"]["reasoning"] = "Localized cutaneous presentation consistent with dermatological care."
    s1["department_section"]["source"] = "slm_department_classifier"
    s1["booking_section"]["patient_name"] = "Alex Johnson"
    print(format_clinical_audit(s1))

    # Case 2: Ambiguous Symptoms
    print()
    s2 = create_empty_schema()
    s2["task"] = "symptom_based_booking"
    s2["symptom_section"]["symptoms"] = ["vaguely unwell", "fatigue", "body aches"]
    s2["department_section"]["is_ambiguous"] = True
    s2["department_section"]["confidence"] = 0.45
    s2["department_section"]["reasoning"] = "Vague multi-system complaints spanning multiple clinical areas."
    s2["department_section"]["source"] = "slm_department_classifier"
    s2["booking_section"]["patient_name"] = "Maria Garcia"
    print(format_clinical_audit(s2))


def run_tests():
    print("\n🧪 Running Full Verification Test Suite (55 tests)...\n")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "agents", "-p", "test_*.py", "-v"])


def main():
    while True:
        print_banner()
        try:
            choice = input("Enter option [0-7]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting HealthOS Demo Suite. Goodbye! 👋\n")
            break

        if choice == "1":
            run_streamlit()
        elif choice == "2":
            run_terminal_chat()
        elif choice == "3":
            run_ambiguity_demo()
        elif choice == "4":
            run_specialist_booking_demo()
        elif choice == "5":
            run_toxicbert_guardrail_demo()
        elif choice == "6":
            run_audit_card_demo()
        elif choice == "7":
            run_tests()
        elif choice in ("0", "exit", "quit"):
            print("\nExiting HealthOS Demo Suite. Goodbye! 👋\n")
            break
        else:
            print("Invalid option. Please choose between 0 and 7.")


if __name__ == "__main__":
    main()

