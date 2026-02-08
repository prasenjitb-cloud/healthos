import slotbooking.ThirdPartyAPIs.booking_system.booking_service
import llama_cpp
import prompts
import json

def load_slm():
    return llama_cpp.Llama(
        model_path="models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        n_ctx=2048,
        temperature=0.2,
        top_p=0.9,
        n_threads=8,
        verbose=False
    )


def analyze_symptoms(llm, symptoms: str) -> dict:
    prompt = prompts.SYSTEM_PROMPT.format(symptoms=symptoms)

    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )

    content = response["choices"][0]["message"]["content"]

    try:
        return json.loads(content)
    except Exception:
        return {
            "description": "Symptoms may be related to a general medical condition.",
            "specialization": "General Medicine"
        }



def main():
    print("\n🩺 Appointment Booking System (Prototype)\n")

    # ---- Step 1: Symptom input ----
    symptoms = input("Please describe your symptoms: ").strip()

    llm = load_slm()
    analysis = analyze_symptoms(llm, symptoms)

    description = analysis["description"]
    specialization = analysis["specialization"]

    if not slotbooking.ThirdPartyAPIs.booking_system.booking_service.specialization_exists(specialization):
        print(
            "\n⚠️ Suggested specialization not available. "
            "Redirecting to General Medicine."
        )
        specialization = "General Medicine"


    print(f"\nℹ️ Info: {description}")
    print(f"👉 Suggested specialization: {specialization}\n")

    # ---- Step 2: Doctor selection (existing logic) ----
    doctors = slotbooking.ThirdPartyAPIs.booking_system.booking_service.get_doctors_by_specialization(specialization)
    if not doctors:
        print("\n❌ No doctors found for this specialization.")
        return

    print("Available doctors:\n")
    for idx, doc in enumerate(doctors, start=1):
        print(f"{idx}. {doc['name']} – {doc['hospital']}")

    try:
        doc_choice = int(input("\nSelect a doctor (number): "))
        selected_doctor = doctors[doc_choice - 1]
    except (ValueError, IndexError):
        print("\n❌ Invalid doctor selection.")
        return

    # ---- Step 3: Slot listing ----
    slots = slotbooking.ThirdPartyAPIs.booking_system.booking_service.get_available_slots(
        selected_doctor["doctor_id"]
    )

    if not slots:
        print("\n❌ No available slots.")
        return

    print("\nAvailable slots:\n")
    for idx, slot in enumerate(slots, start=1):
        print(f"{idx}. {slot['date']} at {slot['time']}")

    try:
        slot_choice = int(input("\nSelect a slot (number): "))
        selected_slot = slots[slot_choice - 1]
    except (ValueError, IndexError):
        print("\n❌ Invalid slot selection.")
        return

    patient_name = input("\nEnter patient name: ")


    success = slotbooking.ThirdPartyAPIs.booking_system.booking_service.book_slot(
        selected_slot["slot_id"],
        patient_name
    )

    if success:
        print(
            f"\n✅ Appointment confirmed with {selected_doctor['name']} "
            f"on {selected_slot['date']} at {selected_slot['time']}"
        )
    else:
        print("\n❌ Slot already booked.")

if __name__ == "__main__":
    main()
