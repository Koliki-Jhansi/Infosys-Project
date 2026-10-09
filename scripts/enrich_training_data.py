import os
import json

def enrich():
    train_path = os.path.join(os.path.dirname(__file__), "..", "data", "training_dataset.json")
    with open(train_path, "r", encoding="utf-8") as f:
        base_train = json.load(f)

    additional = [
        # 1. Booking & Confirmation
        {"text": "Need to confirm my airline reservation and check e-ticket status for PNR", "category": "Booking & Confirmation"},
        {"text": "Minor typo in first name on boarding confirmation e-ticket update", "category": "Booking & Confirmation"},
        {"text": "How do I resend my booking receipt and tax invoice PDF to my email", "category": "Booking & Confirmation"},
        {"text": "Check booking status and view seat assignment in my reservation", "category": "Booking & Confirmation"},
        {"text": "Name correction policy change middle name on passport booking", "category": "Booking & Confirmation"},
        {"text": "Verify 6 character PNR booking reference confirmation on website", "category": "Booking & Confirmation"},
        {"text": "Add passport expiration date and redress number to airline booking", "category": "Booking & Confirmation"},
        {"text": "Did not receive e-ticket confirmation number after booking flight online", "category": "Booking & Confirmation"},
        {"text": "Can I correct misspelled passenger surname on my flight reservation", "category": "Booking & Confirmation"},
        {"text": "Retrieve itinerary and electronic ticket confirmation receipt for expenses", "category": "Booking & Confirmation"},
        {"text": "Booking reference lookup and confirmation email resend", "category": "Booking & Confirmation"},
        {"text": "Passenger name correction and travel document update procedure", "category": "Booking & Confirmation"},
        {"text": "How to download official airline e-ticket receipt with VAT breakdown", "category": "Booking & Confirmation"},
        {"text": "View reservation itinerary schedule and confirmed passenger details", "category": "Booking & Confirmation"},
        {"text": "Link frequent flyer account number to existing flight booking PNR", "category": "Booking & Confirmation"},

        # 2. Check-in & Boarding
        {"text": "How to complete web check in online for domestic and international flights", "category": "Check-in & Boarding"},
        {"text": "When does online check-in open and what is the cutoff time before departure", "category": "Check-in & Boarding"},
        {"text": "How to download and save digital boarding pass to Apple Wallet and Google Pay", "category": "Check-in & Boarding"},
        {"text": "Print physical boarding pass at airport self-service kiosk check-in machine", "category": "Check-in & Boarding"},
        {"text": "Airport security screening liquid restrictions 100ml LAG rule guidelines", "category": "Check-in & Boarding"},
        {"text": "What items are prohibited in cabin hand luggage airport security checkpoint", "category": "Check-in & Boarding"},
        {"text": "Web check-in giving error code booking requires airport desk check-in", "category": "Check-in & Boarding"},
        {"text": "Misplaced printed boarding pass after security how to get replacement at gate", "category": "Check-in & Boarding"},
        {"text": "Boarding gate closing time and group zone boarding sequence rules", "category": "Check-in & Boarding"},
        {"text": "How to use automated bag drop machine after completing mobile check-in", "category": "Check-in & Boarding"},
        {"text": "Self service kiosk not scanning passport barcode for check in", "category": "Check-in & Boarding"},
        {"text": "Can I bring aerosol spray baby milk and medication through airport security", "category": "Check-in & Boarding"},
        {"text": "Lost boarding pass barcode reprint at airline departure gate desk", "category": "Check-in & Boarding"},
        {"text": "Online check in invalid PNR error troubleshooting steps", "category": "Check-in & Boarding"},
        {"text": "Prohibited hazardous items fireworks flares lighter safety matches security rules", "category": "Check-in & Boarding"},

        # 3. Baggage
        {"text": "Checked suitcase did not arrive on baggage carousel filing PIR report", "category": "Baggage"},
        {"text": "Delayed luggage claim Property Irregularity Report desk contact number", "category": "Baggage"},
        {"text": "Lost baggage claim process and compensation for untraced bags after 21 days", "category": "Baggage"},
        {"text": "Damaged suitcase wheel broken cracked shell handle damage inspection report DIR", "category": "Baggage"},
        {"text": "Standard cabin carry on baggage allowance weight and dimension limits", "category": "Baggage"},
        {"text": "Checked baggage allowance rules how many bags and weight per bag allowed", "category": "Baggage"},
        {"text": "Excess baggage charges per kg and pre-booking luggage allowance discount", "category": "Baggage"},
        {"text": "How to transport musical instruments guitar cello sporting golf equipment in hold", "category": "Baggage"},
        {"text": "Pet in cabin and pet in cargo hold travel crate requirements", "category": "Baggage"},
        {"text": "Track delayed luggage status online with 10 character PIR reference code", "category": "Baggage"},
        {"text": "Overweight baggage fee tariff at airport check in counter", "category": "Baggage"},
        {"text": "Suitcase torn zipper broken during baggage transit filing claim", "category": "Baggage"},
        {"text": "Cabin bag size limit overhead bin dimensions 55x40x20cm", "category": "Baggage"},
        {"text": "Baggage delivery to hotel after flight delay reporting", "category": "Baggage"},
        {"text": "Sports gear snowboard surfboard bicycle baggage check in policy", "category": "Baggage"},

        # 4. Delays & Cancellations
        {"text": "Flight delayed over 2 hours meal and beverage refreshment voucher eligibility", "category": "Delays & Cancellations"},
        {"text": "Overnight flight delay hotel accommodation and airport transit shuttle voucher", "category": "Delays & Cancellations"},
        {"text": "Flight cancelled by airline how to rebook next flight or claim travel credit", "category": "Delays & Cancellations"},
        {"text": "Missed connecting flight due to incoming aircraft delay ground assistance", "category": "Delays & Cancellations"},
        {"text": "Flight schedule disruption weather cancellation alternative routing options", "category": "Delays & Cancellations"},
        {"text": "How to collect refreshment vouchers at airline gate during long flight delay", "category": "Delays & Cancellations"},
        {"text": "Free rebooking policy after involuntary flight cancellation", "category": "Delays & Cancellations"},
        {"text": "Airline passenger rights delay compensation reimbursement claim", "category": "Delays & Cancellations"},
        {"text": "Transit passenger stranded at airport due to cancelled connecting flight", "category": "Delays & Cancellations"},
        {"text": "Delayed flight notification rescheduled departure time information", "category": "Delays & Cancellations"},
        {"text": "Severe weather delay meal voucher counter location in terminal concourse", "category": "Delays & Cancellations"},
        {"text": "Emergency flight cancellation open travel voucher validity rules", "category": "Delays & Cancellations"},

        # 5. Refunds & Payments
        {"text": "Credit card charged twice for single flight booking duplicate transaction refund", "category": "Refunds & Payments"},
        {"text": "Refund processing timeline how many days to credit back to original payment method", "category": "Refunds & Payments"},
        {"text": "How to request refund for refundable airline ticket on website", "category": "Refunds & Payments"},
        {"text": "Refund for paid seat selection extra legroom fee after aircraft change", "category": "Refunds & Payments"},
        {"text": "Paid ancillary service refund priority boarding meal pre-order refund", "category": "Refunds & Payments"},
        {"text": "Payment failed but amount deducted from bank account reconciliation", "category": "Refunds & Payments"},
        {"text": "Travel voucher redemption policy convert unused voucher to cash refund", "category": "Refunds & Payments"},
        {"text": "Airport tax and departure fee refund for unused non-refundable flight ticket", "category": "Refunds & Payments"},
        {"text": "Double charge on bank statement resolution dispute support", "category": "Refunds & Payments"},
        {"text": "Involuntary schedule change ancillary fee refund claim process", "category": "Refunds & Payments"},
        {"text": "Credit card payment gateway failure debit reversal turnaround time", "category": "Refunds & Payments"},

        # 6. Airport Facilities
        {"text": "Airport executive lounge access rules locations and single visit day pass fees", "category": "Airport Facilities"},
        {"text": "Short term and long term parking options tariffs and online pre-booking discounts", "category": "Airport Facilities"},
        {"text": "How to transfer between terminal 1 and terminal 2 free airside shuttle train", "category": "Airport Facilities"},
        {"text": "Airport public transit ground transportation subway express bus taxi stands", "category": "Airport Facilities"},
        {"text": "Where are passenger rest zones quiet sleeping pods located in airport terminal", "category": "Airport Facilities"},
        {"text": "Economy parking lot to departure terminal bus schedule frequency", "category": "Airport Facilities"},
        {"text": "Premium business class lounge amenities showers wifi food buffet", "category": "Airport Facilities"},
        {"text": "Car rental counters and return parking garage directions at airport", "category": "Airport Facilities"},
        {"text": "Airport terminal connection inter-terminal automated people mover train", "category": "Airport Facilities"},
        {"text": "Valet parking rates and designated curbside drop off zone location", "category": "Airport Facilities"},

        # 7. Shopping & Services
        {"text": "Airport duty free shopping allowance limits liquor tobacco perfumes international travel", "category": "Shopping & Services"},
        {"text": "Where is the VAT tax refund desk for tourist customs stamp before security", "category": "Shopping & Services"},
        {"text": "Airport dining options certified halal kosher vegan gluten-free restaurants", "category": "Shopping & Services"},
        {"text": "Duty free price matching and pre-order click and collect retail pickup", "category": "Shopping & Services"},
        {"text": "Tourist tax refund invoice validation and cash refund payout counter", "category": "Shopping & Services"},
        {"text": "Food court restaurants opening hours and international cuisines in concourse", "category": "Shopping & Services"},
        {"text": "Customs duty free allowance exemption for international arriving passengers", "category": "Shopping & Services"},
        {"text": "VAT refund office terminal location stamp receipts before check in", "category": "Shopping & Services"},
        {"text": "Special dietary dining food options after airport security screening", "category": "Shopping & Services"},

        # 8. Passenger Assistance
        {"text": "Request electric buggy wheelchair assistance WCHR from curb to boarding gate", "category": "Passenger Assistance"},
        {"text": "Senior citizen elderly traveler assistance and mobility wheelchair escort", "category": "Passenger Assistance"},
        {"text": "Unaccompanied minor UM service procedure for children traveling alone escort", "category": "Passenger Assistance"},
        {"text": "Airport lost and found office location claim misplaced personal belongings", "category": "Passenger Assistance"},
        {"text": "Service animal and guide dog documentation requirements inside aircraft cabin", "category": "Passenger Assistance"},
        {"text": "Special accessibility assistance for passengers with reduced mobility PRM", "category": "Passenger Assistance"},
        {"text": "Left phone or tablet at airport security checkpoint lost property recovery", "category": "Passenger Assistance"},
        {"text": "Traveling with wheelchair battery type and medical equipment pre-notification", "category": "Passenger Assistance"},
        {"text": "Unaccompanied child handover and guardian verification at arrival gate", "category": "Passenger Assistance"},
        {"text": "Certified guide dog cabin travel veterinary vaccination health certificate", "category": "Passenger Assistance"},

        # 9. General Support
        {"text": "Where is the general airport information desk and customer service counter", "category": "General Support"},
        {"text": "Multilingual customer support translation service for international visitors", "category": "General Support"},
        {"text": "Airport hours of operation and terminal public access guidelines", "category": "General Support"},
        {"text": "General feedback and passenger support inquiry help desk", "category": "General Support"},
        {"text": "Information desk terminal directory map and customer care representative", "category": "General Support"},
        {"text": "General passenger inquiries and airport logistics guidance", "category": "General Support"}
    ]

    # Combine ensuring no exact duplicate strings
    seen = set()
    combined = []
    for item in base_train + additional:
        t = item["text"].strip().lower()
        if t not in seen:
            seen.add(t)
            combined.append(item)

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)
    print(f"Successfully enriched training dataset: {len(combined)} samples.")

if __name__ == "__main__":
    enrich()
