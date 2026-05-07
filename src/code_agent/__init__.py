"""Code Agent package"""

import os

from code_agent.core.otlp import init_otlp

if os.getenv("OTLP_ENABLE"):
    init_otlp()
    print("OTLP enabled")
else:
    print("OTLP disabled")
