#!/usr/bin/env python

import asyncio
import ssl
import hashlib
import hmac
import git
import logging

from aiohttp import web

logger = logging.getLogger("WebhookListener")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter("[{asctime}] {name} :: {levelname:>8} :: {message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)

SECRET_TOKEN = open("secret_token", "r").read()


def validate_signature(payload_body: bytes, secret_token: str, signature_header: str) -> bool:
    """Function to validate whether a webhook payload has a valid signature. The signature should be the HMAC-SHA256
    digest of the payload body keyed with a secret token.

    :param payload_body: Body of the POST request
    :param secret_token: A secret token known by authorised originators
    :param signature_header: Hex digest of signature in request headers
    :return: True if valid, otherwise False
    """

    if not signature_header:
        logger.warning("Failed to validate signature: X-Hub-Signature-256 header is missing!")
        return False
    
    hash_object = hmac.new(secret_token.encode("utf8"), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature_header):
        logger.warning("Failed to validate signature: signatures do not match!")
        return False
    
    return True


async def webhook_handler(request: web.Request) -> web.Response:
    """On receipt of a POST request to /webhook, if the signature is valid, this function tries to update the
    repository. Either way, it will send the appropriate response to the originator.

    :param request: HTTP POST request to /webhook.
    :return: HTTP Response (200 if successful, 401 if unauthorised)
    """
    logger.info("Webhook triggered: verifying signature.")
        
    received_signature = request.headers.get("X-Hub-Signature-256")
    request_body = await request.read()
    if validate_signature(request_body, SECRET_TOKEN, received_signature):
        logger.info("Validated signature, pulling repository...")

        repo = git.Repo("/home/nic/Desktop/pi-server")
        current = repo.head.commit
        repo.remotes.origin.pull()
        if current != repo.head.commit:
            logger.info("Repository contents have changed.")
        else:
            logger.info("No change; repository already up-to-date.")

        return web.Response(status=200)
    
    return web.Response(status=401)


async def run_server() -> None:
    app = web.Application()
    app.add_routes([web.post("/webhook", webhook_handler)])

    ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain("certs/cert.pem", "certs/cert.key")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner=runner,
        port=12244,
        ssl_context=ssl_context
    )
    await site.start()
    logger.info("Webhook listener running")

    await asyncio.Event().wait()


if __name__ == "__main__":
    logger.info("Starting webhook listener")
    asyncio.run(run_server())
