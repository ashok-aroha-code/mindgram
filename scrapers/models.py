from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class AbstractMetadata:
    session_name: str = ""
    session_track: str = ""
    session_id: str = ""
    session_type: str = ""
    ce_credit: str = ""
    date: str = ""
    session_time: str = ""
    presentation_time: str = ""
    presentation_id: str = ""
    location: str = ""
    session_description: str = ""
    attendance_type: str = ""

@dataclass
class Abstract:
    link: str = ""
    title: str = ""
    doi: str = ""
    number: str = ""
    author_info: str = ""
    abstract: str = "-"
    abstract_html: str = ""
    abstract_markdown: str = ""
    abstract_metadata: AbstractMetadata = field(default_factory=AbstractMetadata)

@dataclass
class Meeting:
    meeting_name: str = ""
    date: str = ""
    link: str = ""
    abstracts: List[Abstract] = field(default_factory=list)

    def to_dict(self):
        """Converts the object and all nested items into a standard dictionary."""
        return asdict(self)
