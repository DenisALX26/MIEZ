"""Tests for the AgentRunner tool-use loop and tool decorator."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from api.agent import AgentRunner, Tool, agent_tool, get_registry
from api.agent.operations import generate_report
from api.models import Report, User


def _text_block(text):
    return SimpleNamespace(type='text', text=text)


def _tool_use_block(tool_use_id, name, input_data):
    return SimpleNamespace(type='tool_use', id=tool_use_id, name=name, input=input_data)


def _response(stop_reason, content):
    return SimpleNamespace(stop_reason=stop_reason, content=content)


class AgentRunnerLoopTests(TestCase):
    def setUp(self):
        self.ceo = User.objects.create_user(
            username='ceo-loop',
            email='ceo-loop@example.com',
            role=User.Role.CEO,
        )
        self.hr_manager = User.objects.create_user(
            username='hr-manager-loop',
            email='hr-manager-loop@example.com',
            role=User.Role.HR,
            position='HR Manager',
        )

        self.report = Report.objects.create(
            name='HR Headcount',
            slug='hr-headcount-runner',
            category='HR',
            period='May 2026',
        )

    @patch('api.agent.runner.Anthropic')
    def test_run_end_turn_returns_text_immediately(self, mock_anthropic):
        client = mock_anthropic.return_value
        client.messages.create.return_value = _response(
            'end_turn',
            [_text_block('final answer')],
        )

        runner = AgentRunner(self.ceo)
        result = runner.run('hello')

        self.assertEqual(result['response'], 'final answer')
        self.assertEqual(result['tool_calls_made'], [])
        client.messages.create.assert_called_once()

    @patch('api.agent.runner.Anthropic')
    def test_run_tool_use_response_triggers_tool_execution_and_loops(self, mock_anthropic):
        calls = []

        def summarize(module: str, user: User):
            calls.append((module, user.username))
            return {'module': module, 'role': user.role}

        tool = Tool.from_callable(summarize, name='get_dashboard_summary')
        client = mock_anthropic.return_value
        client.messages.create.side_effect = [
            _response('tool_use', [_tool_use_block('tool-1', 'get_dashboard_summary', {'module': 'sales'})]),
            _response('end_turn', [_text_block('sales summary ready')]),
        ]

        runner = AgentRunner(self.ceo, tools=[tool])
        result = runner.run('summarize sales')

        self.assertEqual(result['response'], 'sales summary ready')
        self.assertEqual(calls, [('sales', 'ceo-loop')])
        self.assertEqual(len(result['tool_calls_made']), 1)
        self.assertEqual(result['tool_calls_made'][0]['tool_name'], 'get_dashboard_summary')
        self.assertIsNone(result['tool_calls_made'][0]['error'])
        self.assertIn('module', result['tool_calls_made'][0]['result'])
        self.assertEqual(client.messages.create.call_count, 2)

        second_call_messages = client.messages.create.call_args_list[1].kwargs['messages']
        self.assertEqual(second_call_messages[-1]['role'], 'user')
        self.assertEqual(second_call_messages[-1]['content'][0]['type'], 'tool_result')
        self.assertFalse(second_call_messages[-1]['content'][0]['is_error'])

    def test_get_system_prompt_includes_report_catalog_for_manager(self):
        runner = AgentRunner(self.hr_manager)

        prompt = runner.get_system_prompt()

        self.assertIn('Available report slugs:', prompt)
        self.assertIn('hr-headcount-runner (HR Headcount)', prompt)

    def test_get_tools_for_user_includes_generate_report_for_manager(self):
        runner = AgentRunner(self.hr_manager, tools=get_registry().get_all())

        tool_names = [tool.name for tool in runner.get_tools_for_user()]

        self.assertIn('generate_report', tool_names)

    @patch('api.agent.operations.generate_report_file')
    @patch('api.agent.runner.Anthropic')
    def test_run_generate_report_returns_queued_follow_up(self, mock_anthropic, mocked_generate_file):
        client = mock_anthropic.return_value
        client.messages.create.side_effect = [
            _response('tool_use', [_tool_use_block('tool-1', 'generate_report', {'slug': self.report.slug})]),
        ]

        runner = AgentRunner(self.hr_manager)
        result = runner.run('generate the HR Headcount report')

        self.assertEqual(result['response'], 'The HR Headcount report has been queued. It will be available in Reports shortly.')
        self.assertEqual(len(result['tool_calls_made']), 1)
        self.assertEqual(result['tool_calls_made'][0]['tool_name'], 'generate_report')
        mocked_generate_file.assert_called_once()

    @patch('api.agent.runner.Anthropic')
    def test_run_multiple_sequential_tool_calls_resolved_correctly(self, mock_anthropic):
        execution_order = []

        def first_tool(user: User, value: str):
            execution_order.append(('first', value))
            return f'first:{value}'

        def second_tool(user: User, value: str):
            execution_order.append(('second', value))
            return f'second:{value}'

        runner = AgentRunner(
            self.ceo,
            tools=[
                Tool.from_callable(first_tool, name='first_tool'),
                Tool.from_callable(second_tool, name='second_tool'),
            ],
        )

        client = mock_anthropic.return_value
        client.messages.create.side_effect = [
            _response('tool_use', [_tool_use_block('tool-1', 'first_tool', {'value': 'one'})]),
            _response('tool_use', [_tool_use_block('tool-2', 'second_tool', {'value': 'two'})]),
            _response('end_turn', [_text_block('all done')]),
        ]

        result = runner.run('do the sequence')

        self.assertEqual(result['response'], 'all done')
        self.assertEqual(execution_order, [('first', 'one'), ('second', 'two')])
        self.assertEqual([item['tool_name'] for item in result['tool_calls_made']], ['first_tool', 'second_tool'])
        self.assertEqual(client.messages.create.call_count, 3)

    @patch('api.agent.runner.Anthropic')
    def test_run_max_iterations_reached_returns_fallback_message(self, mock_anthropic):
        runner = AgentRunner(
            self.ceo,
            tools=[Tool.from_callable(lambda value: value, name='loop_tool')],
        )
        runner.MAX_ITERATIONS = 2

        client = mock_anthropic.return_value
        client.messages.create.side_effect = [
            _response('tool_use', [_tool_use_block('tool-1', 'loop_tool', {'value': 'first'})]),
            _response('tool_use', [_tool_use_block('tool-2', 'loop_tool', {'value': 'second'})]),
        ]

        result = runner.run('keep going')

        self.assertIn('could not complete', result['response'])
        self.assertEqual(len(result['tool_calls_made']), 2)
        self.assertEqual(client.messages.create.call_count, 2)

    @patch('api.agent.runner.Anthropic')
    def test_run_tool_raises_exception_error_captured_in_tool_result(self, mock_anthropic):
        def explode(user: User, value: str):
            raise RuntimeError('boom')

        runner = AgentRunner(self.ceo, tools=[Tool.from_callable(explode, name='explode_tool')])
        client = mock_anthropic.return_value
        client.messages.create.side_effect = [
            _response('tool_use', [_tool_use_block('tool-1', 'explode_tool', {'value': 'x'})]),
            _response('end_turn', [_text_block('handled')]),
        ]

        result = runner.run('break it')

        self.assertEqual(result['response'], 'handled')
        self.assertEqual(len(result['tool_calls_made']), 1)
        self.assertEqual(result['tool_calls_made'][0]['error'], 'boom')

        second_call_messages = client.messages.create.call_args_list[1].kwargs['messages']
        self.assertTrue(second_call_messages[-1]['content'][0]['is_error'])
        self.assertIn('boom', second_call_messages[-1]['content'][0]['content'])


class AgentToolDecoratorTests(TestCase):
    def test_agent_tool_decorator_attaches_name_description_schema(self):
        @agent_tool(name='custom_tool', description='Custom tool description')
        def sample_tool(title: str, count: int = 1):
            return f'{title}:{count}'

        metadata = sample_tool.agent_tool

        self.assertEqual(metadata['name'], 'custom_tool')
        self.assertEqual(metadata['description'], 'Custom tool description')
        self.assertEqual(metadata['schema']['type'], 'object')
        self.assertEqual(metadata['schema']['properties']['title']['type'], 'string')
        self.assertEqual(metadata['schema']['properties']['count']['type'], 'integer')
        self.assertEqual(metadata['schema']['required'], ['title'])
