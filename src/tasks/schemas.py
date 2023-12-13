import datetime

from pydantic import BaseModel, field_validator

m_list = ["important", "notes", "links", "completed", "deleted"]


# class TypeTitle(Enum):
#     important = "important"
#     notes = "notes"
#     links = "links"
#     completed = "completed"
#     deleted = "deleted"


class TaskBase(BaseModel):
    title: str  # "important", "notes", "links", "completed", "deleted"
    labelText: str
    do_before: datetime.date
    on_this_day: bool

    @field_validator('title')
    def validate_field(cls, value):
        valid_values = ["important", "notes", "links", "completed", "deleted"]
        if value not in valid_values:
            raise ValueError(f"Invalid value for field. Allowed values are: {valid_values}")
        return value


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True  # orm_mode = True
