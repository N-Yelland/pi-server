#!/usr/bin/env python

import asyncio
import ssl
import hashlib
import hmac
import subprocess

from aiohttp import web

SECRET = open("secret_token", "r").read()
print(SECRET)


def verify_signature(payload_body: str, secret_token: str, signature_header: str) -> bool:

    if not signature_header:
        print("X-Hub-Signature-256 header is missing!")
        return False
    
    hash_object = hmac.new(secret_token.encode("utf8"), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature_header):
        print("Failed to validate signature.")
        return False
    
    print("Signature validated, proceding...")
    return True


async def run_server():
    app = web.Application()

    routes = web.RouteTableDef()

    @routes.get("/webhook")
    async def get_handler(request):
        print("New Connection")
        return web.Response(text="This is the webhook listener.\n", content_type="text/html")
    
    @routes.post("/webhook")
    async def post_handler(request: web.Request):
        print("Webhook triggered, recieving payload:")
        
        print("Verifying signature...")
        recieved_signature = request.headers.get("X-Hub-Signature-256")
        request_body = await request.read()
        if verify_signature(request_body, SECRET, recieved_signature):
            print("Pulling repository...")
            subprocess.Popen("git pull", shell=True, stdout=subprocess.PIPE).communicate()


    app.router.add_routes(routes)

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
    print("Webhook listener running...")

    await asyncio.Event().wait()

if __name__ == "__main__":
    print("Starting webhook listener...")
    asyncio.run(run_server())


"""
Example webhook payload headers

See https://docs.github.com/en/webhooks/webhook-events-and-payloads


<CIMultiDictProxy(
    'Host': 'pi.nicyelland.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip',
    'X-Forwarded-For': '140.82.115.38',
    'CF-RAY': '84cda5f5cf2559d4-IAD',
    'Content-Length': '7297',
    'X-Forwarded-Proto': 'https',
    'CF-Visitor': '{"scheme":"https"}',
    'User-Agent': 'GitHub-Hookshot/547858f',
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'X-GitHub-Delivery': '798321da-be44-11ee-9341-6160b273cb58',
    'X-GitHub-Event': 'push',
    'X-GitHub-Hook-ID': '457504192',
    'X-GitHub-Hook-Installation-Target-ID': '749487659',
    'X-GitHub-Hook-Installation-Target-Type': 'repository',
    'X-Hub-Signature': 'sha1=adfb82aed4868548952c78c040b2c362c41edf1e',
    'X-Hub-Signature-256': 'sha256=0787c13d36202acd81e20cf847ecaee88a6158f3f25c2f53e0e4ef3b39015f68',
    'CF-Connecting-IP': '140.82.115.38',
    'CDN-Loop': 'cloudflare',
    'CF-IPCountry': 'US'
)>
"""