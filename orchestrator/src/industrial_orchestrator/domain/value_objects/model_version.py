"""
MODEL VERSION VALUE OBJECT
Manages versioning for fine-tuned models.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ModelVersion(BaseModel):
    """
    Semantic versioning for fine-tuned models.
    Format: major.minor.patch-build
    """
    major: int = Field(default=1, ge=0)
    minor: int = Field(default=0, ge=0)
    patch: int = Field(default=0, ge=0)
    build: Optional[str] = None
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.build:
            version += f"-{self.build}"
        return version
    
    @classmethod
    def parse(cls, version_str: str) -> 'ModelVersion':
        """Parse version string into ModelVersion object."""
        parts = version_str.split('-')
        semver = parts[0].split('.')
        
        if len(semver) != 3:
            raise ValueError(f"Invalid semver format: {parts[0]}")
            
        return cls(
            major=int(semver[0]),
            minor=int(semver[1]),
            patch=int(semver[2]),
            build=parts[1] if len(parts) > 1 else None
        )
    
    def increment_patch(self) -> 'ModelVersion':
        return self.model_copy(update={"patch": self.patch + 1})
    
    def increment_minor(self) -> 'ModelVersion':
        return self.model_copy(update={"minor": self.minor + 1, "patch": 0})
    
    def increment_major(self) -> 'ModelVersion':
        return self.model_copy(update={"major": self.major + 1, "minor": 0, "patch": 0})
