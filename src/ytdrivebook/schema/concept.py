"""Graph contracts: the nodes (Concept), typed edges (Relation), and the
hyperedge (a taught segment, the unit of evidence) of the Concept Hyper-Lattice."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from ytdrivebook.schema.source import MediaRef


class RelationType(str, Enum):
    """Edge vocabulary. The edge types determine what the graph can answer."""

    PREREQUISITE = "prerequisite"   # directed: forms the teaching partial order
    EXPLAINS = "explains"
    CONTRADICTS = "contradicts"     # the misconception this idea corrects
    EXAMPLE_OF = "example_of"
    SAME_AS = "same_as"             # alias resolution across videos
    RELATED = "related"             # weighted similarity


class Relation(BaseModel):
    to: str  # target concept id
    type: RelationType
    weight: float = 1.0


class Concept(BaseModel):
    """A node in the idea map. Aggregates every unit (across videos) about it."""

    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    definition: str | None = None
    relations: list[Relation] = Field(default_factory=list)
    unit_refs: list[str] = Field(default_factory=list)
    merged_from: list[str] = Field(
        default_factory=list, description="audit trail for concept resolution (ADR-0007)"
    )


class Hyperedge(BaseModel):
    """One taught segment connecting several concepts at once. Carries the
    timestamp + frame, so it is the citable unit of evidence in an answer."""

    id: str
    concept_ids: list[str]
    unit_ref: str
    start: float | None = None
    end: float | None = None
    media: list[MediaRef] = Field(default_factory=list)
