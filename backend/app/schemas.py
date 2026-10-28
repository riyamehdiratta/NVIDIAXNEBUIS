from pydantic import BaseModel, Field


class TextSource(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)
    filename: str = "Pasted note.txt"


class ScanRequest(BaseModel):
    source_ids: list[str] = Field(default_factory=list)
    skill_id: str = "commitment-scan"
    allow_remote: bool = False
    preview_id: str | None = None


class DecisionRequest(BaseModel):
    decision: str
    title: str | None = None
    detail: str | None = None
    due_at: str | None = None
    owner: str | None = None
    override_reason: str | None = Field(default=None, max_length=1000)


class PolicyRequest(BaseModel):
    mode: str | None = None
    autonomy_level: int | None = Field(default=None, ge=0, le=4)
    shadow_mode: bool | None = None
    max_actions_per_day: int | None = Field(default=None, ge=1, le=100)
    life_area: str | None = None


class AutonomyControlRequest(BaseModel):
    enabled: bool


class ScamCheckRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)


class FamilyProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    relationship: str = Field(default="trusted contact", max_length=80)
    verification_phrase: str = Field(min_length=8, max_length=200)


class FamilyVerifyRequest(BaseModel):
    member_id: str
    verification_phrase: str = Field(min_length=1, max_length=200)


class QuietHoursContractRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=12, max_length=500)
    scope: str = "all_auto"


class SkillRequest(BaseModel):
    name: str
    description: str
    instructions: str
    enabled: bool = True


class ActionRequest(BaseModel):
    loop_id: str | None = None
    action_type: str
    title: str
    payload: dict = Field(default_factory=dict)
