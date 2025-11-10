"""
Configuration File
Default settings for IB to DSR automation
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Base directory
BASE_DIR = Path(__file__).parent

# Default file paths (can be overridden by CLI args)
DEFAULT_IB_PDF = BASE_DIR / 'investigative_brochure.pdf'
DEFAULT_TEMPLATE = BASE_DIR / 'Drug_Safety_Report_Template.docx'
DEFAULT_MAPPING = BASE_DIR / 'IB_to_DSR_Manual_Mapping.md'
DEFAULT_OUTPUT = BASE_DIR / 'data' / 'output' / 'DSR_Pralsetinib_Populated.docx'

# Directory structure
DATA_DIR = BASE_DIR / 'data'
INPUT_DIR = DATA_DIR / 'input'
INTERMEDIATE_DIR = DATA_DIR / 'intermediate'
OUTPUT_DIR = DATA_DIR / 'output'

# Processing options
FORCE_REINDEX = False
USE_AI_EXTRACTION = True

# OpenAI Settings
AI_MODEL = 'gpt-4-turbo-preview'  # or 'gpt-3.5-turbo' for faster/cheaper
MAX_TOKENS = 2000
TEMPERATURE = 0.3  # Lower = more deterministic

# Rate limiting
API_DELAY_SECONDS = 0.5  # Delay between API calls to avoid rate limits

# Validation settings
MIN_CONTENT_LENGTH = 10
MAX_CONTENT_LENGTH = 20000

