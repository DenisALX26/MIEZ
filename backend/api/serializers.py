from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.utils import timezone

from .models import Department, User
from .models import Product
from .models import Report
from .models import Supplier, StockMovement
from .models import Ticket, Order, OrderItem, Customer, Invoice
from .models import SystemStatus
from .models import ConversationSession, ConversationMessage


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'slug', 'icon', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmployeeListSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'position',
            'employment_type',
            'start_date',
            'salary_ron',
            'address',
            'role',
            'is_active',
            'full_time',
            'department',
        ]

    def get_department(self, obj):
        if obj.department is None:
            return None
        return {
            'id': obj.department.id,
            'name': obj.department.name,
            'slug': obj.department.slug,
        }


class EmployeeCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='An employee with this email already exists.',
            )
        ]
    )

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'department',
            'position',
            'employment_type',
            'start_date',
            'salary_ron',
            'address',
            'is_active',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone': {'required': True},
            'role': {'required': False},
            'department': {'required': True},
            'position': {'required': True},
            'employment_type': {'required': True},
            'start_date': {'required': True},
            'salary_ron': {'required': True},
            'address': {'required': True},
            'is_active': {'required': True},
        }

    def validate_phone(self, value):
        if not value.startswith('+40'):
            raise serializers.ValidationError('Phone number must start with +40.')
        return value

    def create(self, validated_data):
        email = validated_data.pop('email').lower().strip()
        base_username = email.split('@')[0] or 'employee'
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{counter}'
            counter += 1

        explicit_role = validated_data.pop('role', None)
        employment_type = validated_data.pop('employment_type', User.EmploymentType.FULL_TIME)
        validated_data['full_time'] = employment_type == User.EmploymentType.FULL_TIME

        department = validated_data.get('department')
        role = User.Role.SALES
        if department is not None:
            department_slug = (getattr(department, 'slug', '') or '').strip().lower()
            department_name = (getattr(department, 'name', '') or '').strip().lower()

            if 'it' in department_slug or 'it' in department_name:
                role = User.Role.IT
            elif 'sales' in department_slug or 'sales' in department_name:
                role = User.Role.SALES
            elif 'hr' in department_slug or 'hr' in department_name:
                role = User.Role.HR
            elif 'inventory' in department_slug or 'inventory' in department_name:
                role = User.Role.INVENTORY

        if explicit_role:
            role = explicit_role

        user = User.objects.create(
            username=username,
            email=email,
            role=role,
            employment_type=employment_type,
            **validated_data,
        )
        user.set_unusable_password()
        user.save(update_fields=['password'])
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'category', 'stock_count', 'min_stock', 'unit_price_ron', 'created_at']
        read_only_fields = ['id', 'created_at']


class SalesProductSerializer(serializers.ModelSerializer):
    availability = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'category', 'unit_price_ron', 'stock_count', 'availability']

    def get_availability(self, obj):
        return obj.availability


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_email', 'contact_phone', 'address', 'created_at']
        read_only_fields = ['id', 'created_at']


class StockMovementSerializer(serializers.ModelSerializer):
    # Accept product and supplier as PKs on write, but include nested objects on read
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all(), allow_null=True, required=False)
    product_obj = ProductSerializer(source='product', read_only=True)
    supplier_obj = SupplierSerializer(source='supplier', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = StockMovement
        fields = ['id', 'movement_type', 'product', 'product_obj', 'product_name', 'product_sku', 'supplier', 'supplier_obj', 'supplier_name', 'quantity', 'expected_date', 'notes', 'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'product_obj', 'supplier_obj', 'product_name', 'product_sku', 'supplier_name', 'created_by_username']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and not validated_data.get('created_by'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class OrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer',
            'customer_name',
            'value_ron',
            'date',
            'status',
            'channel',
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer',
            'value_ron',
            'date',
            'status',
            'channel',
            'notes',
        ]
        read_only_fields = ['id', 'order_number']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class OrderItemDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    line_total_ron = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_sku',
            'quantity',
            'unit_price_ron',
            'line_total_ron',
        ]

    def get_line_total_ron(self, obj):
        return obj.quantity * obj.unit_price_ron


class OrderDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    items = OrderItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer',
            'customer_name',
            'created_by',
            'created_by_username',
            'value_ron',
            'date',
            'status',
            'channel',
            'notes',
            'created_at',
            'updated_at',
            'items',
        ]


class CustomerSalesSummarySerializer(serializers.ModelSerializer):
    total_value_ron = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    orders_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'contact_name',
            'location',
            'tier',
            'orders_count',
            'total_value_ron',
        ]


class CustomerOrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'value_ron',
            'date',
            'status',
            'channel',
        ]


class CustomerDetailSerializer(serializers.ModelSerializer):
    orders = CustomerOrderHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'contact_name',
            'contact_email',
            'contact_phone',
            'address',
            'location',
            'tier',
            'notes',
            'created_at',
            'updated_at',
            'orders',
        ]


class InvoiceListSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_name = serializers.CharField(source='order.customer.name', read_only=True)
    effective_status = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'order',
            'order_number',
            'customer_name',
            'amount_ron',
            'status',
            'effective_status',
            'issued_date',
            'due_date',
        ]

    def get_effective_status(self, obj):
        today = timezone.localdate()
        if obj.due_date and obj.due_date < today and obj.status != Invoice.Status.PAID:
            return 'OVERDUE'
        return obj.status


class TicketSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    requested_for_username = serializers.CharField(source='requested_for.username', read_only=True, allow_null=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_number',
            'title',
            'description',
            'category',
            'priority',
            'status',
            'department',
            'department_name',
            'requested_by',
            'requested_by_username',
            'requested_for',
            'requested_for_username',
            'assigned_to',
            'assigned_to_username',
            'location',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = ['id', 'ticket_number', 'created_at', 'updated_at', 'resolved_at']


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_number',
            'title',
            'description',
            'category',
            'priority',
            'status',
            'department',
            'requested_for',
            'assigned_to',
            'location',
            'requested_by',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = ['id', 'ticket_number', 'status', 'requested_by', 'created_at', 'updated_at', 'resolved_at']
        extra_kwargs = {
            'title': {'required': True, 'allow_blank': False},
            'description': {'required': True, 'allow_blank': False},
            'category': {'required': False},
            'priority': {'required': False},
            'department': {'required': False},
            'requested_for': {'required': False, 'allow_null': True},
            'assigned_to': {'required': False, 'allow_null': True},
            'location': {'required': False},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['requested_by'] = request.user
        validated_data['status'] = Ticket.Status.OPEN
        return super().create(validated_data)


class TicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'status', 'assigned_to', 'resolved_at']
        read_only_fields = ['id', 'resolved_at']

    def validate_status(self, value):
        if self.instance is None:
            return value

        current = self.instance.status
        allowed_transitions = {
            Ticket.Status.OPEN: [Ticket.Status.IN_PROGRESS],
            Ticket.Status.IN_PROGRESS: [Ticket.Status.RESOLVED],
            Ticket.Status.RESOLVED: [],
            Ticket.Status.CLOSED: [],
        }

        if value == current:
            return value

        if value not in allowed_transitions.get(current, []):
            raise serializers.ValidationError(f'Invalid transition from {current} to {value}.')

        return value

    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        if new_status == Ticket.Status.IN_PROGRESS and not validated_data.get('assigned_to'):
            request = self.context.get('request')
            if request and request.user and request.user.is_authenticated:
                validated_data['assigned_to'] = request.user

        return super().update(instance, validated_data)


class ReportSerializer(serializers.ModelSerializer):
    file_available = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ['id', 'name', 'slug', 'category', 'period', 'file_size_kb', 'generated_at', 'file_available', 'digest_data']

    def get_file_available(self, obj):
        return bool(obj.file_path)


class SystemStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemStatus
        fields = ['id', 'name', 'uptime_pct', 'status', 'last_incident_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatMessageHistorySerializer(serializers.Serializer):
    """Serializer for a single message in conversation history."""
    role = serializers.ChoiceField(choices=['user', 'assistant'])
    content = serializers.CharField()


class AssistantChatRequestSerializer(serializers.Serializer):
    """Serializer for the assistant chat endpoint request."""
    message = serializers.CharField(required=True)
    history = ChatMessageHistorySerializer(many=True, required=False, allow_empty=True)

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError('Message cannot be empty.')
        if len(value) > 4000:
            raise serializers.ValidationError('Message cannot exceed 4000 characters.')
        return value


class ToolCallSerializer(serializers.Serializer):
    """Serializer for tool calls made by the agent."""
    tool_name = serializers.CharField()
    arguments = serializers.JSONField()


class AssistantChatResponseSerializer(serializers.Serializer):
    """Serializer for the assistant chat endpoint response."""
    response = serializers.CharField()
    tool_calls_made = ToolCallSerializer(many=True, allow_empty=True)


class ConversationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMessage
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationSessionSerializer(serializers.ModelSerializer):
    messages = ConversationMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ConversationSession
        fields = ['id', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConversationSessionListSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source='messages.count', read_only=True)
    preview = serializers.SerializerMethodField()

    def get_preview(self, obj):
        first = obj.messages.filter(role='user').first()
        return first.content[:80] if first else ''

    class Meta:
        model = ConversationSession
        fields = ['id', 'created_at', 'updated_at', 'message_count', 'preview']
        read_only_fields = fields
