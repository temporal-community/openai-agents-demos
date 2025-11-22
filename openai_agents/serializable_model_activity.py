"""Serializable ModelActivity wrapper to fix MockValSer pydantic serialization issues."""

from typing import Any, Dict, List, Optional

from agents.items import ModelResponse
from pydantic import BaseModel
from temporalio import activity
from temporalio.contrib.openai_agents._invoke_model_activity import ActivityModelInput
from temporalio.contrib.openai_agents._invoke_model_activity import (
    ModelActivity as BaseModelActivity,
)


class SerializableUsage(BaseModel):
    """Pydantic model for Usage to ensure proper serialization."""

    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    input_tokens_details: Dict[str, Any] = {}
    output_tokens_details: Dict[str, Any] = {}

    @classmethod
    def from_usage(cls, usage: Any) -> "SerializableUsage":
        """Convert Usage object to serializable format."""
        requests = getattr(usage, "requests", 0)
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)

        # Handle input_tokens_details
        input_tokens_details: Dict[str, Any] = {}
        input_details = getattr(usage, "input_tokens_details", None)
        if input_details:
            try:
                if hasattr(input_details, "__dict__"):
                    input_tokens_details = dict(input_details.__dict__)
                elif hasattr(input_details, "model_dump"):
                    input_tokens_details = input_details.model_dump()
                elif isinstance(input_details, dict):
                    input_tokens_details = dict(input_details)
            except Exception:
                input_tokens_details = {}

        # Handle output_tokens_details
        output_tokens_details: Dict[str, Any] = {}
        output_details = getattr(usage, "output_tokens_details", None)
        if output_details:
            try:
                if hasattr(output_details, "__dict__"):
                    output_tokens_details = dict(output_details.__dict__)
                elif hasattr(output_details, "model_dump"):
                    output_tokens_details = output_details.model_dump()
                elif isinstance(output_details, dict):
                    output_tokens_details = dict(output_details)
            except Exception:
                output_tokens_details = {}

        return cls(
            requests=requests,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_tokens_details=input_tokens_details,
            output_tokens_details=output_tokens_details,
        )


class SerializableModelResponse(BaseModel):
    """Pydantic model for ModelResponse to ensure proper serialization."""

    output: List[Dict[str, Any]]
    usage: SerializableUsage
    response_id: Optional[str] = None

    @classmethod
    def from_model_response(cls, response: Any) -> "SerializableModelResponse":
        """Convert a ModelResponse dataclass to a serializable Pydantic model."""
        # Convert output items to dictionaries to avoid pydantic serialization issues
        output_dicts = []
        for item in response.output:
            try:
                if hasattr(item, "model_dump"):
                    # This is a Pydantic model, convert to dict safely
                    # Use mode='json' to avoid MockValSer issues
                    output_dicts.append(
                        item.model_dump(mode="json", exclude_unset=True)
                    )
                elif hasattr(item, "__dict__"):
                    # Convert dataclass to dict
                    output_dicts.append(dict(item.__dict__))
                else:
                    # Already a dict or primitive
                    output_dicts.append(item)
            except Exception as e:
                # Fallback: create a simple dict representation
                output_dicts.append(
                    {
                        "error": f"Serialization failed: {str(e)}",
                        "type": str(type(item).__name__),
                    }
                )

        # Convert usage to serializable format safely
        try:
            usage = SerializableUsage.from_usage(response.usage)
        except Exception as e:
            # Fallback: create default usage if conversion fails
            usage = SerializableUsage()

        return cls(output=output_dicts, usage=usage, response_id=response.response_id)


class SerializableModelActivity(BaseModelActivity):
    """ModelActivity wrapper that returns serializable responses."""

    @activity.defn
    async def invoke_model_activity(self, input: ActivityModelInput) -> ModelResponse:
        """Activity that invokes a model and returns a serializable response."""
        # Call the parent implementation to get the ModelResponse
        response = await super().invoke_model_activity(input)

        # Convert to serializable format
        return SerializableModelResponse.from_model_response(response)  # type: ignore[return-value]
