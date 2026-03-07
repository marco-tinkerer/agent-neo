"""Configuration settings for Agent Neo."""

import os

# HEF Model Paths
# Function-calling optimized model (preferred)
HEF_PATH_FC = "/home/marcomark/hailo-models/Qwen2-1.5B-Instruct-Function-Calling-v1.hef"
# General instruct model
HEF_PATH_GEN = "/home/marcomark/hailo-models/Qwen2.5-1.5B-Instruct.hef"

# Active HEF Path
HEF_PATH = os.environ.get("HEF_PATH", HEF_PATH_FC)

# Request settings
REQUEST_TIMEOUT = 120.0  # seconds

# Model settings
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.1
