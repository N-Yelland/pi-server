from hashlib import sha3_512

class AuthenticationError(Exception):
    """Exception to be raised when authenication fails (for whatever reason)"""


def authetnicate(password: str, verifier_filepath: str) -> None:
    """Function to perform authentication of a given password against a given verifier file.
    Raises an Autnetication error if there are any problems in authentiation. Otherwise, does nothing.

    :param password: password to authenticate.
    :param verifier_filepath: path to verifier file, which contains <salt>:<hash> in hexadecimal.
    :raises AuthenticationError: in the event that authentication fails.
    """
    if not password:
        raise AuthenticationError("Password not provided")

    with open(verifier_filepath, "r") as f:
        salt, verifier = f.read().split(":")
    
    password_hash = sha3_512(password.encode() + bytes.fromhex(salt)).hexdigest()

    if password_hash != verifier:
        raise AuthenticationError("Incorrect password")
