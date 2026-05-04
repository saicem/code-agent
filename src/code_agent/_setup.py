from code_agent import monitoring
from code_agent.core.config import get_config

if get_config().logging.otlp_enabled:
    monitoring.init()
