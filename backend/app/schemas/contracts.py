from typing import Any, Literal

from pydantic import BaseModel, Field

Family = Literal["sql", "mql", "cql", "es_dsl", "cypher"]
Confidence = Literal["high", "medium", "low"]
SemanticType = Literal[
    "id",
    "code",
    "category",
    "measure",
    "timestamp",
    "date",
    "text",
    "personal_data",
    "flag",
    "other",
]


class ValueCount(BaseModel):
    value: str
    count: int | None = None


class FieldInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    references: str | None = None
    distinct_count: int | None = None
    top_values: list[ValueCount] = Field(default_factory=list)
    description: str | None = None
    semantic_type: SemanticType | None = None
    sensitive: bool = False
    value_meanings: dict[str, str] | None = None
    confidence: Confidence | None = None
    reviewed: bool = False


class EntityInfo(BaseModel):
    name: str
    kind: Literal["table", "collection", "index", "node_label", "edge_type"] = "table"
    description: str | None = None
    row_count: int | None = None
    fields: list[FieldInfo] = Field(default_factory=list)
    partition_keys: list[str] = Field(default_factory=list)
    clustering_keys: list[str] = Field(default_factory=list)
    reviewed: bool = False


class RelationshipInfo(BaseModel):
    source: str
    target: str
    via: str | None = None


class SchemaSnapshot(BaseModel):
    connection_id: str
    engine: str
    family: Family
    namespace: str | None = None
    entities: list[EntityInfo]
    relationships: list[RelationshipInfo] = Field(default_factory=list)

    def entity(self, name: str) -> EntityInfo:
        return next(e for e in self.entities if e.name == name)


class ColumnDescription(BaseModel):
    name: str
    description: str
    semantic_type: SemanticType
    sensitive: bool = False
    value_meanings: dict[str, str] | None = None
    confidence: Confidence


class TableDescription(BaseModel):
    table_description: str
    columns: list[ColumnDescription]


class CostEstimate(BaseModel):
    risk: Literal["low", "medium", "high"] = "low"
    estimated_rows: int | None = None
    detail: str | None = None


class ResultSet(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool = False
