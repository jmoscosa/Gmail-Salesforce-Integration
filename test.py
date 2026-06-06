from gmail_sync.sender_parser import parse_sender

test_senders = [
    "Lev from ReciPal <lev@recipal.com>",
    "Marriott Bonvoy <marriottbonvoy@email-marriott.com>",
    "Sarah Young <sarah.y@qualifinane.com>",
    "no-reply@email.claude.com",
    "",
]

for s in test_senders:
    name, email = parse_sender(s)
    print(f"  raw:   {s!r}")
    print(f"  name:  {name!r}")
    print(f"  email: {email!r}")
    print()