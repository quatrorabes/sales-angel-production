MESSAGES = {
    "linkedin": "⏰ Only 17 spots left in CRE beta (3 taken this morning)",
    "email": "P.S. - First 20 users get lifetime lock at $29/mo",
    "text": "Dude, built that CRE intelligence thing. Want in before it fills?"
}

for platform, msg in MESSAGES.items():
    print(f"{platform.upper()}: {msg}\n")
