"""
Agent runner for the MIEZ Assistant.

This module provides the AgentRunner class that orchestrates AI agent interactions
with the MIEZ system, including tool registration, conversation management, and
system prompt injection based on user role.
"""

from __future__ import annotations

from typing import Optional, Any

try:
    from anthropic import Anthropic  # type: ignore
except ImportError:  # pragma: no cover - patched in tests when anthropic is absent
    Anthropic = None

from .tools import get_tool, get_registry
from .operations import can_generate_reports
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
    
    SYSTEM_PROMPT_TEMPLATE = """You are MIEZ Assistant, an AI assistant embedded in the MIEZ business management system.

Current user: {display_name}{position_line}{department_line}
Role: {role}
{page_line}
Available report slugs: {report_catalog}

Tone and behaviour:
- Be professional, concise, and helpful.
- Answer only within your tool set. If asked something you cannot do, say so clearly and suggest what you can help with instead.
- Respond in the same language the user writes in (Romanian or English).
- When you queue a report with generate_report(slug), reply exactly: The {{report_name}} report has been queued. It will be available in Reports shortly.

You have access to tools scoped to this user's role. Do not attempt actions outside the provided tools."""

    MODEL_NAME = 'claude-haiku-4-5-20251001'
    MAX_ITERATIONS = 10
    
    # Role-to-permissions mapping
    ROLE_PERMISSIONS = {
        User.Role.CEO: [
            'view_all_dashboards',
            'view_financial_reports',
            'manage_employees',
            'view_all_departments',
            'access_system_settings',
            'view_sales_reports',
            'manage_tickets',
            'manage_stock',
            'process_leave_requests',
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
        ],
        User.Role.INVENTORY: [
            'view_inventory_dashboard',
            'manage_stock',
            'manage_products',
            'manage_suppliers',
            'view_stock_movements',
        ],
    }
    
    def __init__(self, user: User, tools: Optional[list] = None, current_page: str = ''):
        self.user = user
        self.tools = tools or []
        self.current_page = current_page
        self._system_prompt = None

    def get_system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self._build_system_prompt()
        return self._system_prompt

    def _build_system_prompt(self) -> str:
        full_name = self.user.get_full_name().strip() or self.user.username
        position = getattr(self.user, 'position', '') or ''
        position_line = f', {position}' if position else ''

        department = getattr(self.user, 'department', None)
        department_name = department.name if department else ''
        department_line = f'\nDepartment: {department_name}' if department_name else ''

        page_line = f'Current page: {self.current_page}' if self.current_page else ''

        report_catalog = self._build_report_catalog()

        return self.SYSTEM_PROMPT_TEMPLATE.format(
            display_name=full_name,
            position_line=position_line,
            department_line=department_line,
            role=self.user.get_role_display(),
            page_line=page_line,
            report_catalog=report_catalog,
        )
    
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
        """Execute the Anthropic-backed agent loop.

        The loop handles assistant text responses, tool execution cycles, tool
        errors, and a bounded retry count to avoid unbounded recursion.
        """
        if Anthropic is None:
            return {
                'response': f'[STUB] Processing message: {message}',
                'tool_calls_made': [],
            }

        client = Anthropic()
        conversation = self._build_initial_conversation(message=message, history=history)
        tool_calls_made: list[dict[str, Any]] = []

        for iteration in range(self.MAX_ITERATIONS):
            response = client.messages.create(
                model=self.MODEL_NAME,
                max_tokens=1024,
                system=self.get_system_prompt(),
                messages=conversation,
                tools=[tool.to_dict() for tool in tools],
            )

            text_response = self._extract_text_response(response)
            tool_uses = self._extract_tool_uses(response)

            if not tool_uses or getattr(response, 'stop_reason', None) == 'end_turn':
                return {
                    'response': text_response,
                    'tool_calls_made': tool_calls_made,
                }

            assistant_content = self._normalize_response_content(getattr(response, 'content', []))
            if assistant_content:
                conversation.append({'role': 'assistant', 'content': assistant_content})

            tool_result_blocks = []
            for tool_use in tool_uses:
                tool_name = tool_use.get('name')
                tool_input = tool_use.get('input', {}) or {}
                tool_identifier = tool_use.get('id')
                try:
                    tool = self._resolve_tool(tool_name, tools)
                    result = tool.execute(user=self.user, **tool_input)
                    serialized_result = result if isinstance(result, str) else self._stringify_result(result)
                    tool_call_record = {
                        'tool_name': tool_name,
                        'arguments': tool_input,
                        'result': serialized_result,
                        'error': None,
                    }
                    tool_result_blocks.append({
                        'type': 'tool_result',
                        'tool_use_id': tool_identifier,
                        'content': serialized_result,
                        'is_error': False,
                    })
                except Exception as exc:  # pragma: no cover - exercised through tests
                    serialized_result = str(exc)
                    tool_call_record = {
                        'tool_name': tool_name,
                        'arguments': tool_input,
                        'result': None,
                        'error': serialized_result,
                    }
                    tool_result_blocks.append({
                        'type': 'tool_result',
                        'tool_use_id': tool_identifier,
                        'content': serialized_result,
                        'is_error': True,
                    })

                tool_calls_made.append(tool_call_record)

            conversation.append({'role': 'user', 'content': tool_result_blocks})

            if len(tool_uses) == 1 and tool_calls_made and tool_calls_made[-1]['tool_name'] == 'generate_report' and tool_calls_made[-1]['error'] is None:
                return {
                    'response': self._format_report_generation_response(tool_calls_made[-1]['result']),
                    'tool_calls_made': tool_calls_made,
                }

        return {
            'response': 'The assistant could not complete the request after several tool iterations.',
            'tool_calls_made': tool_calls_made,
        }

    def _build_initial_conversation(self, message: str, history: list) -> list:
        conversation = []
        for entry in history:
            conversation.append({'role': entry.get('role'), 'content': entry.get('content')})
        conversation.append({'role': 'user', 'content': message})
        return conversation

    @staticmethod
    def _extract_text_response(response: Any) -> str:
        content_blocks = getattr(response, 'content', []) or []
        text_parts = []
        for block in content_blocks:
            block_type = getattr(block, 'type', None) or block.get('type')
            if block_type == 'text':
                text_parts.append(getattr(block, 'text', None) or block.get('text', ''))
        return ''.join(text_parts)

    @staticmethod
    def _extract_tool_uses(response: Any) -> list[dict[str, Any]]:
        content_blocks = getattr(response, 'content', []) or []
        tool_uses = []
        for block in content_blocks:
            block_type = getattr(block, 'type', None) or block.get('type')
            if block_type != 'tool_use':
                continue
            tool_uses.append({
                'id': getattr(block, 'id', None) or block.get('id'),
                'name': getattr(block, 'name', None) or block.get('name'),
                'input': getattr(block, 'input', None) or block.get('input', {}),
            })
        return tool_uses

    @staticmethod
    def _normalize_response_content(content: list[Any]) -> list[dict[str, Any]]:
        normalized = []
        for block in content or []:
            block_type = getattr(block, 'type', None) or block.get('type')
            if block_type == 'text':
                normalized.append({'type': 'text', 'text': getattr(block, 'text', None) or block.get('text', '')})
            elif block_type == 'tool_use':
                normalized.append({
                    'type': 'tool_use',
                    'id': getattr(block, 'id', None) or block.get('id'),
                    'name': getattr(block, 'name', None) or block.get('name'),
                    'input': getattr(block, 'input', None) or block.get('input', {}),
                })
        return normalized

    def _resolve_tool(self, tool_name: str, tools: list) -> Any:
        for tool in tools:
            if getattr(tool, 'name', None) == tool_name:
                return tool

        registry_tool = get_tool(tool_name)
        if registry_tool is not None:
            return registry_tool

        registry_tool = get_registry().get(tool_name)
        if registry_tool is not None:
            return registry_tool

        raise ValueError(f'Tool {tool_name} is not registered')

    @staticmethod
    def _stringify_result(result: Any) -> str:
        if isinstance(result, (dict, list)):
            import json

            return json.dumps(result, default=str)
        return str(result)

    @staticmethod
    def _format_report_generation_response(result: Any) -> str:
        report_name = 'report'
        if isinstance(result, dict):
            report_name = str(result.get('report_name') or report_name)
        elif isinstance(result, str) and result.strip():
            report_name = result.strip()
        return f'The {report_name} report has been queued. It will be available in Reports shortly.'

    def _build_report_catalog(self) -> str:
        from api.models import Report

        if not can_generate_reports(self.user):
            return 'none'

        report_items = Report.objects.order_by('name').values_list('slug', 'name')
        catalog = [f'{slug} ({name})' for slug, name in report_items]
        return ', '.join(catalog) if catalog else 'none'
    
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
            if (
                tool.name == 'generate_report' and can_generate_reports(self.user)
            ) or (
                tool.name != 'generate_report' and (
                    not getattr(tool, 'required_permission', None)
                    or tool.required_permission in user_permissions
                )
            )
        ]
        
        return available_tools
