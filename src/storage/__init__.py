"""
Storage & Persistence Package for Network Attack Forecast System.
Provides OperationLogger to record, persist, and retrieve CSV ingestion runs and state records.
"""

from src.storage.operation_logger import OperationLogger

__all__ = ["OperationLogger"]
