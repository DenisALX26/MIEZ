"""
Tool registry and management for the MIEZ Agent.

Provides a centralized registry for managing agent tools, including
registration, validation, and access control based on user roles.
"""

from typing import List, Dict, Optional, Callable, Any


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
    
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given arguments.
        
        Args:
            **kwargs: Tool-specific arguments
        
        Returns:
            Tool execution result
        """
        if self.execute_fn is None:
            raise NotImplementedError(f"Tool {self.name} does not have an execute function")
        return self.execute_fn(**kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool to dictionary representation.
        
        Returns:
            Dict with tool metadata
        """
        return {
            'name': self.name,
            'description': self.description,
            'required_permission': self.required_permission,
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
