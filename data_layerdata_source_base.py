"""
Base class for all data sources with standardized interface and error handling
"""

import abc
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Enumeration of data source types"""
    MARKET_DATA = "market_data"
    ALTERNATIVE_DATA = "