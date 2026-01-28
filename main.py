import booking.booking_service
import core.chatbot
import booking.validators

def main():
    print("\n🩺 Appointment Booking System (Prototype)\n")

    # ---- Step 1: Symptom input ----
    symptoms = input("Please describe your symptoms: ").strip()

    if not booking.validators.validate_non_empty(symptoms, "Symptoms"):
        return

    if not booking.validators.validate_min_length(symptoms, 5, "Symptoms"):
        return

    slm = core.slm.load_slm()
    analysis = core.slm.analyze_symptoms(slm, symptoms)

    description = analysis["description"]
    specialization = analysis["specialization"]

    if not booking.booking_service.specialization_exists(specialization):
        print(
            "\n⚠️ Suggested specialization not available. "
            "Redirecting to General Medicine."
        )
        specialization = "General Medicine"


    print(f"\nℹ️ Info: {description}")
    print(f"👉 Suggested specialization: {specialization}\n")

    # ---- Step 2: Doctor selection (existing logic) ----
    doctors = booking.booking_service.get_doctors_by_specialization(specialization)
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
    slots = booking.booking_service.get_available_slots(
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

    if not booking.validators.validate_non_empty(patient_name, "Patient name"):
        return


    success = booking.booking_service.book_slot(
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
