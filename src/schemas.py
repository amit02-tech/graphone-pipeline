from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SourceInfo(BaseModel):
    name: str
    url: str


class PricingModel(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"
    ENTERPRISE = "ENTERPRISE"


# --- 1. Startup Entity ---
class StartupData(BaseModel):
    employeeCount: Optional[int] = None


class StartupContent(BaseModel):
    entityName: str
    data: StartupData = Field(default_factory=StartupData)


class StartupEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "STARTUP"
    source: SourceInfo
    content: StartupContent
    collectedAt: str = Field(default_factory=utc_now_iso)


# --- 2. Product Entity ---
class ProductContent(BaseModel):
    startupName: str
    productName: Optional[str] = None
    pricingModel: PricingModel = PricingModel.FREEMIUM


class ProductEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "PRODUCT"
    source: SourceInfo
    content: ProductContent
    collectedAt: str = Field(default_factory=utc_now_iso)


# --- 3. Research Paper Entity ---
class ResearchPaperContent(BaseModel):
    title: str
    authors: List[str]
    paper_url: str
    github_url: Optional[str] = None
    github_stars: Optional[int] = None
    published_date: str  # ISO-8601


class ResearchPaperEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "RESEARCH_PAPER"
    source: SourceInfo
    content: ResearchPaperContent
    collectedAt: str = Field(default_factory=utc_now_iso)


# --- 4. Job Entity ---
class JobContent(BaseModel):
    company: str
    title: Optional[str] = None
    date: str  # ISO-8601
    is_remote: bool = False
    role_family: str = "Engineering"


class JobEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "JOB"
    source: SourceInfo
    content: JobContent
    collectedAt: str = Field(default_factory=utc_now_iso)


# --- 5. News Entity ---
class NewsContent(BaseModel):
    title: str
    published_date: str  # ISO-8601
    full_text: str


class NewsEntity(BaseModel):
    schemaVersion: str = "1.0"
    recordType: str = "NEWS"
    source: SourceInfo
    content: NewsContent
    collectedAt: str = Field(default_factory=utc_now_iso)