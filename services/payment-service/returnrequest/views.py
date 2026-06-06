from django.core.exceptions import ValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext as _
from rest_framework.filters import SearchFilter
from admin_api.permissions import require_permission
from orders.models import Shipment
from .models import BalanceWithdrawRequest, ReturnRequest, Transaction
from .permissions import (IsAssignedDeliveryPerson, IsRequestSupplier,
                          IsReturnRequestOwner)
from .serializers import (BalanceWithdrawRequestSerializer,
                          ReturnRequestCreateSerializer,
                          ReturnRequestDetailSerializer,
                          ReturnRequestListSerializer, TransactionSerializer)
from .services import ReturnRequestService
from .tasks import (
    process_supplier_approval_task,  
    approve_withdrawal_task,
    cancel_return_request_task,
    create_withdrawal_request_task,
    reject_return_request_task,
    reject_withdrawal_task
)


class ReturnRequestViewSet(viewsets.ModelViewSet):
    queryset = ReturnRequest.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['reason', 'user__email', 'order__order_number']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return ReturnRequest.objects.none()
        queryset = ReturnRequest.objects.for_user(user).select_related(
            'user', 'product__Supplier', 'order'
        ).prefetch_related('shipments')
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ReturnRequestCreateSerializer
        if self.action in ['list', 'new', 'accepted', 'rejected']:
            return ReturnRequestListSerializer
        return ReturnRequestDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            ReturnRequestService.create_return_request_logic(
                user_id=request.user.id,
                product_id=serializer.validated_data['product'].id,
                order_id=serializer.validated_data['order'].id,
                quantity=serializer.validated_data['quantity'],
                reason=serializer.validated_data['reason'],
                image=serializer.validated_data.get('image') 
            )
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': _("An error occurred while processing your request.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            {"message": _("Your return request has been created successfully.")},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def new(self, request):
        queryset = self.get_queryset().filter(status=ReturnRequest.ReturnStatus.NEW)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def accepted(self, request):
        queryset = self.get_queryset().filter(status=ReturnRequest.ReturnStatus.ACCEPTED)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def rejected(self, request):
        rejected_statuses = [
            ReturnRequest.ReturnStatus.REJECTED,
            ReturnRequest.ReturnStatus.CANCELLED
        ]
        queryset = self.get_queryset().filter(status__in=rejected_statuses)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsRequestSupplier])
    def approve(self, request, pk=None):
        self.get_object() # Enforce object-level permissions
        process_supplier_approval_task.delay(pk)
        return Response({'status': _('Approval is being processed.')}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'], permission_classes=[IsRequestSupplier])
    def reject(self, request, pk=None):
        self.get_object() # Enforce object-level permissions
        reject_return_request_task.delay(pk)
        return Response({'status': _('Rejection is being processed.')}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'], permission_classes=[IsReturnRequestOwner])
    def cancel(self, request, pk=None):
        self.get_object() # Enforce object-level permissions
        cancel_return_request_task.delay(pk)
        return Response({'status': _('Cancellation is being processed.')}, status=status.HTTP_202_ACCEPTED)


class BalanceWithdrawRequestViewSet(mixins.CreateModelMixin,
                                      mixins.ListModelMixin,
                                      mixins.RetrieveModelMixin,
                                      viewsets.GenericViewSet):
    serializer_class = BalanceWithdrawRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return BalanceWithdrawRequest.objects.none()
        if user.is_staff:
            return BalanceWithdrawRequest.objects.all()
        return BalanceWithdrawRequest.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check balance synchronously before queuing the task
        amount = serializer.validated_data['amount']
        if request.user.Balance < amount:
            return Response(
                {"message": _("Insufficient balance for this withdrawal.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Proceed to task only if balance is sufficient
        create_withdrawal_request_task.delay(
            user_id=request.user.id,
            amount=str(amount),
            transfer_number=serializer.validated_data['transfer_number'],
            transfer_type=serializer.validated_data['transfer_type'],
            notes=serializer.validated_data.get('notes')
        )
        
        return Response(
            {"message": _("Your withdrawal request is being processed.")},
            status=status.HTTP_202_ACCEPTED
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser, require_permission('accounts.can_approve_withdrawals')])
    def approve(self, request, pk=None):
        admin_notes = request.data.get('admin_notes', '')
        approve_withdrawal_task.delay(pk, request.user.id, admin_notes)
        return Response({'status': _('Approval is being processed.')}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser, require_permission('accounts.can_approve_withdrawals')])
    def reject(self, request, pk=None):
        admin_notes = request.data.get('admin_notes')
        if not admin_notes:
            return Response({'detail': _('Admin notes are required for rejection.')}, status=status.HTTP_400_BAD_REQUEST)
        
        reject_withdrawal_task.delay(pk, request.user.id, admin_notes)
        return Response({'status': _('Rejection is being processed.')}, status=status.HTTP_202_ACCEPTED)


class TransactionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Transaction.objects.none()
        if user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=self.request.user)