from dataclasses import dataclass


@dataclass
class StepOutcome:
    step_type: str
    ok: bool
    details: str
    required: bool = True
