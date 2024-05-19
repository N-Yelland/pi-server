#!/usr/bin/env python

from random import randbytes
from getpass import getpass
from hashlib import sha3_512

SALT_SIZE = 16
VERIFIER_FILE = "private/quizdle_verifier"

salt = randbytes(16)

while True:
    password = getpass("\t  Enter password: ")
    if password == "":
        print("Password cannot be empty.")
        continue
    check = getpass("\tConfirm password: ")
    if password != check:
        print("Passwords must match.")
        continue
    break

verifier = sha3_512(password.encode() + salt).hexdigest()

with open(VERIFIER_FILE, "w") as f:
    f.write(salt.hex() + ":" + verifier)

print(f"Password changed successfully (Verifier stored in {VERIFIER_FILE})")
