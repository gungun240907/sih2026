import sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, 'reconfigure'):
        _s.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
import os
load_dotenv()
print(repr(os.getenv("GMAIL_ADDRESS")))