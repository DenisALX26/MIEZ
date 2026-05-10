"""
Tool registry and management for the MIEZ Agent.

Provides a centralized registry for managing agent tools, including
registration, validation, and access control based on user roles.
"""

from __future__ import annotations

import inspect
import types
import typing
from typing import List, Dict, Optional, Callable, Any, Union, get_args, get_origin


def _annotation_to_json_schema(annotation: Any) -> Dict[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Handle X | None and Union[X, Y, None]
    is_union = origin is Union or isinstance(annotation, types.UnionType)
    if is_union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _annotation_to_json_schema(non_none[0])
        return {'type': 'string'}

    if annotation is int:
        return {'type': 'integer'}
    if annotation is float:
        return {'type': 'number'}
    if annotation is bool:
        return {'type': 'boolean'}
    if annotation is list or origin is list:
        item_annotation = args[0] if args else Any
        return {'type': 'array', 'items': _annotation_to_json_schema(item_annotation)}
    if annotation is dict or origin is dict:
        return {'type': 'object'}
    return {'type': 'string'}


def build_schema_from_callable(func: Callable) -> Dict[str, Any]:
    signature = inspect.signature(func)
    try:
        hints = typing.get_type_hints(func)
    except Exception:
        hints = {}
    properties: Dict[str, Any] = {}
    required: List[str] = []

    for parameter_name, parameter in signature.parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if parameter_name == 'user':
            continue
        annotation = hints.get(parameter_name, Any)
        properties[parameter_name] = _annotation_to_json_schema(annotation)
        if parameter.default is inspect._empty:
            required.append(parameter_name)

    return {
        'type': 'object',
        'properties': properties,
        'required': required,
    }


def agent_tool(name: Optional[str] = None, description: Optional[str] = None, schema: Optional[Dict[str, Any]] = None):
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or (inspect.getdoc(func) or '').strip()
        tool_schema = schema or build_schema_from_callable(func)
        func.agent_tool = {
            'name': tool_name,
            'description': tool_description,
            'schema': tool_schema,
        }
        return func

    return decorator


class Tool:
    """
    Base class for agent tools.
    
    Each tool represents a capability the agent can use to interact
    with the MIEZ system or retrieve information.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        required_permission: Optional[str] = None,
        execute_fn: Optional[Callable] = None,
        schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a tool.
        
        Args:
            name: Unique tool identifier
            description: Human-readable tool description
            required_permission: Required permission to use this tool (optional)
            execute_fn: Callable that executes the tool logic
        """
        self.name = name
        self.description = description
        self.required_permission = required_permission
        self.execute_fn = execute_fn
        self.schema = schema or {}

    @classmethod
    def from_callable(
        cls,
        func: Callable,
        required_permission: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> 'Tool':
        tool_meta = getattr(func, 'agent_tool', {})
        return cls(
            name=name or tool_meta.get('name') or func.__name__,
            description=description or tool_meta.get('description') or (inspect.getdoc(func) or '').strip(),
            required_permission=required_permission,
            execute_fn=func,
            schema=schema or tool_meta.get('schema') or build_schema_from_callable(func),
        )
    
    def can_use(self, permissions: List[str]) -> bool:
        """
        Check if user with given permissions can use this tool.
        
        Args:
            permissions: List of user permissions
        
        Returns:
            True if user can use this tool
        """
        if not self.required_permission:
            return True
        return self.required_permission in permissions
    
    def execute(self, user: Any = None, **kwargs) -> Any:
        """
        Execute the tool with given arguments.
        
        Args:
            **kwargs: Tool-specific arguments
        
        Returns:
            Tool execution result
        """
        if self.execute_fn is None:
            raise NotImplementedError(f"Tool {self.name} does not have an execute function")

        call_kwargs = dict(kwargs)
        signature = inspect.signature(self.execute_fn)
        if 'user' in signature.parameters and 'user' not in call_kwargs:
            call_kwargs['user'] = user

        return self.execute_fn(**call_kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool to dictionary representation.
        
        Returns:
            Dict with tool metadata
        """
        return {
            'name': self.name,
            'description': self.description,
            'input_schema': self.schema,
        }


class ToolRegistry:
    """
    Central registry for managing agent tools.
    
    Maintains all available tools and provides methods for:
    - Registering new tools
    - Retrieving tools by name or role
    - Validating tool access based on permissions
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool instance to register
        
        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
        
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)
    
    def get_all(self) -> List[Tool]:
        """
        Get all registered tools.
        
        Returns:
            List of all tool instances
        """
        return list(self._tools.values())
    
    def get_available(self, permissions: List[str]) -> List[Tool]:
        """
        Get tools available to user with given permissions.
        
        Args:
            permissions: List of user permissions
        
        Returns:
            List of accessible tools
        """
        return [
            tool for tool in self._tools.values()
            if tool.can_use(permissions)
        ]
    
    def get_available_names(self, permissions: List[str]) -> List[str]:
        """
        Get names of tools available to user.
        
        Args:
            permissions: List of user permissions
        
        Returns:
            List of accessible tool names
        """
        return [tool.name for tool in self.get_available(permissions)]
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert registry to dictionary representation.
        
        Returns:
            Dict mapping tool names to tool metadata
        """
        return {name: tool.to_dict() for name, tool in self._tools.items()}


# Global tool registry instance
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    Get or create the global tool registry.
    
    Returns:
        The global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: Tool) -> None:
    """
    Register a tool in the global registry.
    
    Args:
        tool: Tool instance
    """
    get_registry().register(tool)


def get_tool(name: str) -> Optional[Tool]:
    """
    Get a tool from the global registry.
    
    Args:
        name: Tool name
    
    Returns:
        Tool instance or None
    """
    return get_registry().get(name)
