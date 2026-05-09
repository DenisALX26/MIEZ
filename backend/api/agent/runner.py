"""
Agent runner for the MIEZ Assistant.

This module provides the AgentRunner class that orchestrates AI agent interactions
with the MIEZ system, including tool registration, conversation management, and
system prompt injection based on user role.
"""

from typing import Optional

from django.contrib.auth import get_user_model

User = get_user_model()


class AgentRunner:
    """
    Main agent runner for MIEZ Assistant.
    
    Orchestrates AI agent interactions, including:
    - System prompt generation with role-specific information
    - Tool registration and management
    - Conversation history handling
    - Response generation with tool call tracking
    """
    
    # System prompt template - to be replaced with actual agent system prompt
    SYSTEM_PROMPT_TEMPLATE = """You are the MIEZ Assistant, an intelligent agent for the MIEZ business system.
You have access to various tools to help users with their tasks across different departments.

User Role: {role}
User Permissions: {permissions}

You should:
1. Help users with their specific departmental tasks
2. Use available tools appropriately when needed
3. Provide clear and actionable responses
4. Respect role-based permissions

Available tools will be provided in the conversation context."""
    
    # Role-to-permissions mapping
    ROLE_PERMISSIONS = {
        User.Role.CEO: [
            'view_all_dashboards',
            'view_financial_reports',
            'manage_employees',
            'view_all_departments',
            'access_system_settings',
        ],
        User.Role.HR: [
            'manage_employees',
            'view_hr_dashboard',
            'process_leave_requests',
            'manage_attendance',
            'view_payroll',
        ],
        User.Role.SALES: [
            'view_sales_dashboard',
            'manage_orders',
            'manage_customers',
            'manage_invoices',
            'view_sales_reports',
        ],
        User.Role.IT: [
            'view_it_dashboard',
            'manage_tickets',
            'view_system_status',
            'manage_tickets',
        ],
        User.Role.INVENTORY: [
            'view_inventory_dashboard',
            'manage_stock',
            'manage_products',
            'manage_suppliers',
            'view_stock_movements',
        ],
    }
    
    def __init__(self, user: User, tools: Optional[list] = None):
        """
        Initialize the agent runner.
        
        Args:
            user: The Django User object making the request
            tools: Optional list of available tools for the agent
        """
        self.user = user
        self.tools = tools or []
        self._system_prompt = None
    
    def get_system_prompt(self) -> str:
        """
        Generate the system prompt with role-specific information.
        
        Returns:
            The system prompt string with user role and permissions injected.
        """
        if self._system_prompt is None:
            permissions = self.ROLE_PERMISSIONS.get(self.user.role, [])
            permissions_str = ', '.join(permissions) if permissions else 'none'
            
            self._system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
                role=self.user.get_role_display(),
                permissions=permissions_str,
            )
        
        return self._system_prompt
    
    def register_tools(self, tools: list) -> None:
        """
        Register available tools for the agent.
        
        Args:
            tools: List of tool definitions/configurations
        """
        self.tools = tools
    
    def run(self, message: str, history: Optional[list] = None) -> dict:
        """
        Execute the agent with a user message and conversation history.
        
        This is the main entry point that should be replaced with actual
        agent execution logic once the AI agent framework is integrated.
        
        Args:
            message: The user's current message
            history: Optional conversation history as list of dicts with 'role' and 'content'
        
        Returns:
            A dict with keys:
            - response: str - The agent's response
            - tool_calls_made: list - Any tool calls made during execution
        """
        return self._call_anthropic(message=message, history=history or [], tools=self.get_tools_for_user())

    def _call_anthropic(self, message: str, history: list, tools: list) -> dict:
        """Execute the Anthropic-backed agent call.

        Tests can patch this method directly to avoid any external API dependency.
        """
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError:
            return {
                'response': f'[STUB] Processing message: {message}',
                'tool_calls_made': [],
            }

        _ = Anthropic()
        return {
            'response': f'[STUB] Processing message: {message}',
            'tool_calls_made': [],
        }
    
    def get_tools_for_user(self) -> list:
        """
        Get the list of tools available for the current user based on their role.
        
        Returns:
            List of tool definitions filtered by role permissions.
        """
        user_permissions = self.ROLE_PERMISSIONS.get(self.user.role, [])
        
        # Filter tools by user permissions
        available_tools = [
            tool for tool in self.tools
            if not hasattr(tool, 'required_permission') or tool.required_permission in user_permissions
        ]
        
        return available_tools
