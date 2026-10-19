from enum import StrEnum


class RunTriggerEnum(StrEnum):
    MANUAL = "MANUAL"
    SCHEDULER = "SCHEDULER"


class RunStatusEnum(StrEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
