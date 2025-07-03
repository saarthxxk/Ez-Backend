from django.core.signing import TimestampSigner, SignatureExpired, BadSignature

signer = TimestampSigner()

def generate_email_token(username):
    return signer.sign(username)

def verify_email_token(token, max_age=3600):  # 1 hour expiry
    try:
        username = signer.unsign(token, max_age=max_age)
        return username
    except (SignatureExpired, BadSignature):
        return None
