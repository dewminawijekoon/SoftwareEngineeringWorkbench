"""Data models for the Solution Architecture Generator."""
from typing import List, Optional
from pydantic import BaseModel, Field


class UserRequirement(BaseModel):
    """Model for user requirements."""
    requirement: str = Field(..., description="User requirement statement")
    priority: Optional[str] = Field(None, description="Priority level (High/Medium/Low)")
    category: Optional[str] = Field(None, description="Requirement category")


class SupportingDocument(BaseModel):
    """Model for supporting documents."""
    filename: str = Field(..., description="Name of the document")
    content: str = Field(..., description="Extracted content from the document")
    document_type: Optional[str] = Field(None, description="Type of document")


class ArchitectureComponent(BaseModel):
    """Model for architecture components."""
    name: str = Field(..., description="Component name")
    description: str = Field(..., description="Component description")
    technology: Optional[str] = Field(None, description="Suggested technology/framework")
    reasoning: str = Field(..., description="Reason for including this component")


class SolutionArchitecture(BaseModel):
    """Model for the complete solution architecture."""
    overview: str = Field(..., description="High-level architecture overview")
    components: List[ArchitectureComponent] = Field(..., description="Architecture components")
    architecture_pattern: str = Field(..., description="Chosen architecture pattern")
    pattern_reasoning: str = Field(..., description="Reasoning for the pattern choice")
    technology_stack: dict = Field(..., description="Recommended technology stack")
    scalability_considerations: str = Field(..., description="Scalability approach")
    security_considerations: str = Field(..., description="Security measures")
    deployment_strategy: str = Field(..., description="Deployment approach")
    trade_offs: str = Field(..., description="Trade-offs and decisions made")
