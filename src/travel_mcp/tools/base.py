"""Base tool class for Travel MCP Server."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolExecutionContext(BaseModel):
    """Context passed to tool execution."""

    request_id: str
    tool_name: str
    arguments: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, context: ToolExecutionContext) -> Dict[str, Any]:
        """
        Execute the tool with given context.

        Returns a dictionary with the tool's response.
        """
        pass

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input data against the tool's input schema.

        Raises ValidationError if validation fails.
        """
        # Use pydantic to validate if schema is defined
        if self.input_schema:
            from pydantic import ValidationError as PydanticValidationError

            try:
                input_model = self._create_input_model()
                input_model.model_validate(data)
            except PydanticValidationError as e:
                from travel_mcp.core.error_handler import ValidationError

                raise ValidationError(str(e))

    def _create_input_model(self) -> type[BaseModel]:
        """Create a pydantic model from the input schema."""
        schema = self.input_schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        field_definitions = {}
        for field_name, field_info in properties.items():
            field_type = field_info.get("type", "str")
            description = field_info.get("description", "")
            default = ... if field_name in required else None

            # Map JSON types to Python types
            python_type: type = str
            if field_type == "integer":
                python_type = int
            elif field_type == "number":
                python_type = float
            elif field_type == "boolean":
                python_type = bool
            elif field_type == "array":
                python_type = list
            elif field_type == "object":
                python_type = dict

            field_definitions[field_name] = (
                python_type,
                default if default is not ... else Field(default=default, description=description),
            )

        return type("InputModel", (BaseModel,), field_definitions)
