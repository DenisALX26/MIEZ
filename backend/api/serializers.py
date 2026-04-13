from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Department, User
from .models import Product
from .models import Supplier, StockMovement
from .models import Ticket, Order, OrderItem


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

        employment_type = validated_data.pop('employment_type', User.EmploymentType.FULL_TIME)
        validated_data['full_time'] = employment_type == User.EmploymentType.FULL_TIME

        user = User.objects.create(
            username=username,
            email=email,
            role=User.Role.SALES,
            employment_type=employment_type,
            **validated_data,
        )
        user.set_unusable_password()
        user.save(update_fields=['password'])
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'category', 'stock_count', 'min_stock', 'created_at']
        read_only_fields = ['id', 'created_at']


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


class TicketSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_number',
            'title',
            'description',
            'priority',
            'status',
            'department',
            'department_name',
            'requested_by',
            'requested_by_username',
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
            'priority',
            'status',
            'department',
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
