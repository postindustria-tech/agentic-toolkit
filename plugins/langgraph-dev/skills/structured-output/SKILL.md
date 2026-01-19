---
name: structured-output-with-pydantic
description: This skill should be used when the user asks about "structured output", "Pydantic", "output parsing", "data validation", "PydanticOutputParser", "with_structured_output", or needs guidance on extracting structured data from LLM responses.
version: 0.3.3
---

# Structured Output with Pydantic

Pydantic models enable type-safe, validated structured data extraction from LLM outputs.

## Basic Pattern

```python
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

class MovieReview(BaseModel):
    """A structured movie review with rating and summary."""
    title: str = Field(description="Movie title")
    year: int = Field(description="Release year")
    rating: float = Field(ge=0, le=10, description="Rating 0-10")
    summary: str = Field(description="Brief review summary")

# Initialize LLM
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Create structured output wrapper
# Default: method="function_calling" (more compatible, uses tool calling)
# Alternative: method="json_schema" uses Claude's native structured output (beta)
#             Provides guaranteed schema adherence for Sonnet 4.5/Opus 4.1+
llm_with_structure = llm.with_structured_output(MovieReview)

response = llm_with_structure.invoke("Review of The Matrix")
# response is a MovieReview instance
print(response.title)   # "The Matrix"
print(response.year)    # 1999
print(response.rating)  # 8.5
# For debugging: include_raw=True returns {"raw": ..., "parsed": ..., "parsing_error": ...}
```

## PydanticOutputParser (Alternative)

```python
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic

# Define the Pydantic model (same as Basic Pattern, or import from your models module)
class MovieReview(BaseModel):
    """A structured movie review with rating and summary."""
    title: str = Field(description="Movie title")
    year: int = Field(description="Release year")
    rating: float = Field(ge=0, le=10, description="Rating 0-10")
    summary: str = Field(description="Brief review summary")

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
parser = PydanticOutputParser(pydantic_object=MovieReview)

# Create prompt with format instructions
prompt = PromptTemplate(
    template="Extract movie review.\n{format_instructions}\n\nText: {text}",
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# Create chain and invoke
chain = prompt | llm | parser
result = chain.invoke({"text": "The Matrix is a 1999 sci-fi masterpiece..."})
```

## Error Handling

```python
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_anthropic import ChatAnthropic

# Define the Pydantic model
class MovieReview(BaseModel):
    """A structured movie review with rating and summary."""
    title: str = Field(description="Movie title")
    year: int = Field(description="Release year")
    rating: float = Field(ge=0, le=10, description="Rating 0-10")
    summary: str = Field(description="Brief review summary")

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
parser = PydanticOutputParser(pydantic_object=MovieReview)

# Get raw LLM output that needs parsing
prompt = "Review The Matrix (1999). Include title, year, rating (0-10), and summary."
llm_output = llm.invoke(prompt).content

try:
    result = parser.parse(llm_output)
except OutputParserException as e:
    print(f"Parsing failed: {e}")
    # Option 1: Return a default value
    result = None
    # Option 2: Use OutputFixingParser (requires additional LLM call)
    from langchain.output_parsers import OutputFixingParser
    fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)
    result = fixing_parser.parse(llm_output)
```

## In LangGraph

```python
from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

# Define the Pydantic model for structured extraction
class MovieReview(BaseModel):
    """A structured movie review with rating and summary."""
    title: str = Field(description="Movie title")
    year: int = Field(description="Release year")
    rating: float = Field(ge=0, le=10, description="Rating 0-10")
    summary: str = Field(description="Brief review summary")

class ExtractionState(TypedDict):
    text: str
    extracted: MovieReview | None

# Initialize LLM (typically done at module level or passed via config)
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def extract_node(state: ExtractionState) -> dict:
    """Extract structured movie review from text."""
    llm_structured = llm.with_structured_output(MovieReview)
    result = llm_structured.invoke(state["text"])
    return {"extracted": result}
```

## Validation

```python
from pydantic import BaseModel, Field, field_validator, ValidationError

class UserData(BaseModel):
    """User data with validated email and age fields."""
    email: str = Field(description="User's email address")
    age: int = Field(description="User's age in years")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError('Age must be between 0 and 150')
        return v

# Handling validation errors
try:
    user = UserData(email="invalid-email", age=25)
except ValidationError as e:
    print(f"Validation failed: {e.error_count()} error(s)")
    for error in e.errors():
        print(f"  - {error['loc'][0]}: {error['msg']}")
```

## Complex Models

```python
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

class Author(BaseModel):
    """An author with name and biographical information."""
    name: str = Field(description="Author's full name")
    bio: str = Field(description="Brief biography")

class Book(BaseModel):
    """A book with authors, publication details, and genres."""
    title: str = Field(description="Book title")
    authors: list[Author] = Field(description="List of authors")
    publication_year: int = Field(description="Year of publication")
    genres: list[str] = Field(description="Literary genres")

# Initialize LLM and extract structured data
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
llm_with_structure = llm.with_structured_output(Book)

result = llm_with_structure.invoke("Tell me about 1984 by George Orwell")
```

## Best Practices

1. **Prefer `with_structured_output`** - Native structured output for modern LLMs (recommended over PydanticOutputParser)
2. **Add field descriptions** - Help LLM understand what to extract
3. **Add model docstrings** - Provides context to the LLM about the schema
4. **Use validators** - Ensure data quality with custom validation logic
5. **Handle parse errors** - Catch OutputParserException for malformed LLM output
6. **Handle validation errors** - Catch ValidationError for invalid data
7. **Start simple** - Add complexity incrementally
