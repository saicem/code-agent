"""Code Agent package"""

import os

import code_agent.monitoring as monitoring

if os.getenv("OTLP_ENABLED") == "true":
    monitoring.init()
    print("OTLP enabled")
else:
    print("OTLP disabled")
