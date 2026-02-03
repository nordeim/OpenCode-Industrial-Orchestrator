from pydantic import BaseModel

class DomainEntity(BaseModel):
    """Base class for all domain entities"""
    class Config:
        arbitrary_types_allowed = True
