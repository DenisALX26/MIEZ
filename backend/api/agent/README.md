# MIEZ Agent Module

Dedicated module for the MIEZ Assistant agent infrastructure, providing tools, execution orchestration, and role-based access control.

## Directory Structure

```
api/agent/
├── __init__.py       # Module exports
├── runner.py         # AgentRunner orchestration
└── tools.py          # Tool registry and framework
```

## Modules

### `runner.py` - Agent Orchestration

**Main Class**: `AgentRunner`

Orchestrates AI agent interactions with the MIEZ system.

```python
from api.agent import AgentRunner

agent = AgentRunner(user=request.user)
agent.register_tools([...])
response = agent.run(message="Hello", history=[...])
```

**Key Methods**:
- `get_system_prompt()` - Generate role-aware system prompt
- `register_tools(tools)` - Register available tools
- `run(message, history)` - Execute agent with message
- `get_tools_for_user()` - Get role-filtered tools

**Features**:
- Role-based system prompt injection
- Permission-based tool filtering
- Stateless design (no session storage)
- Tool registration interface

---

### `tools.py` - Tool Framework & Registry

**Main Classes**:

#### `Tool`
Base class for creating agent tools.

```python
from api.agent import Tool

tool = Tool(
    name="sales_report",
    description="Generate sales reports",
    required_permission="view_sales_reports",
    execute_fn=generate_sales_report
)
```

**Methods**:
- `can_use(permissions)` - Check if user can use tool
- `execute(**kwargs)` - Execute tool logic
- `to_dict()` - Serialize tool metadata

#### `ToolRegistry`
Central registry for managing tools.

```python
from api.agent import get_registry

registry = get_registry()
registry.register(my_tool)
available_tools = registry.get_available(user_permissions)
```

**Methods**:
- `register(tool)` - Register a tool
- `get(name)` - Get tool by name
- `get_all()` - Get all tools
- `get_available(permissions)` - Get role-filtered tools
- `to_dict()` - Serialize registry

#### Global Functions
- `get_registry()` - Get or create global registry
- `register_tool(tool)` - Register in global registry
- `get_tool(name)` - Get tool from global registry

---

## Usage Examples

### Creating a Custom Tool

```python
from api.agent import Tool, register_tool

def get_employee_list(department: str = None):
    """Fetch employee list from database"""
    from api.models import User
    employees = User.objects.all()
    if department:
        employees = employees.filter(department__name=department)
    return [e.to_dict() for e in employees]

employee_tool = Tool(
    name="get_employees",
    description="List employees, optionally filtered by department",
    required_permission="manage_employees",
    execute_fn=get_employee_list
)

register_tool(employee_tool)
```

### Using AgentRunner with Tools

```python
from api.agent import AgentRunner, get_registry

def process_chat(request):
    # Create agent for user
    agent = AgentRunner(user=request.user)
    
    # Register tools (or use global registry)
    tools = get_registry().get_available(
        agent.ROLE_PERMISSIONS.get(request.user.role, [])
    )
    agent.register_tools(tools)
    
    # Run agent
    response = agent.run(
        message="List all HR employees",
        history=[...]
    )
    
    return response
```

### Tool with Complex Logic

```python
from api.agent import Tool, register_tool
from api.models import Order
from datetime import datetime, timedelta

def get_sales_trend(days: int = 7):
    """Calculate sales trend for the last N days"""
    cutoff = datetime.now() - timedelta(days=days)
    orders = Order.objects.filter(date__gte=cutoff)
    
    daily_totals = {}
    for order in orders:
        date_key = order.date.strftime('%Y-%m-%d')
        daily_totals[date_key] = daily_totals.get(date_key, 0) + float(order.value_ron)
    
    return {
        'period_days': days,
        'daily_totals': daily_totals,
        'total_revenue': sum(daily_totals.values()),
    }

sales_trend_tool = Tool(
    name="sales_trend",
    description="Get sales trend over specified number of days",
    required_permission="view_sales_reports",
    execute_fn=get_sales_trend
)

register_tool(sales_trend_tool)
```

---

## Integration with Chat Endpoint

The `AssistantChatView` uses the agent module:

```python
# api/views.py
from .agent import AgentRunner

class AssistantChatView(APIView):
    def post(self, request):
        agent = AgentRunner(user=request.user)
        
        # TODO: Register tools
        # agent.register_tools([...])
        
        result = agent.run(message=message, history=history)
        return Response(result)
```

---

## Role-Based Permissions

The `AgentRunner` defines role-to-permissions mapping:

| Role | Permissions |
|------|-------------|
| CEO | `view_all_dashboards`, `view_financial_reports`, `manage_employees`, `view_all_departments`, `access_system_settings` |
| HR | `manage_employees`, `view_hr_dashboard`, `process_leave_requests`, `manage_attendance`, `view_payroll` |
| SALES | `view_sales_dashboard`, `manage_orders`, `manage_customers`, `manage_invoices`, `view_sales_reports` |
| IT | `view_it_dashboard`, `manage_tickets`, `view_system_status` |
| INVENTORY | `view_inventory_dashboard`, `manage_stock`, `manage_products`, `manage_suppliers`, `view_stock_movements` |

Add new permissions by extending `AgentRunner.ROLE_PERMISSIONS`.

---

## Future Enhancements

1. **Tool Caching**: Cache tool registry per role
2. **Tool Versioning**: Support multiple versions of tools
3. **Tool Scheduling**: Allow tools to be scheduled/async
4. **Tool Chains**: Define sequences of tool calls
5. **Tool Validation**: Validate tool inputs/outputs
6. **Tool Metrics**: Track tool usage and performance
7. **Tool Dependencies**: Define tool dependencies
8. **Custom Tool Framework**: Enhanced base class with hooks

---

## See Also

- [MIEZ Assistant Chat API](../ASSISTANT_CHAT_API.md)
- [Agent Views](../views.py#AssistantChatView)
- [Agent Tests](../tests/test_assistant_chat.py)
