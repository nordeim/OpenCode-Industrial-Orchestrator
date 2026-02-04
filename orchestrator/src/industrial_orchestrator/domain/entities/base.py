from pydantic import BaseModel, ConfigDict

class DomainEntity(BaseModel):
    """Base class for all domain entities"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
