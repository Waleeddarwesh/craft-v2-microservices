"""
Admin API Views — Dashboard backend endpoints.
All views require IsAdminUser permission (is_staff=True).
"""
import os
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .permissions import IsDashboardUser
from .permissions import require_permission
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from reviews.models import Review

from accounts.models import User, Customer, Supplier, Delivery
from course.models import Course, Enrollment
from notifications.models import Notification
from orders.models import Order, OrderItem, Coupon
from payment.models import PaymentHistory
from products.models import Product, ProImage
from returnrequest.models import ReturnRequest, Transaction, BalanceWithdrawRequest
from reviews.models import Review
from audit_logs.models import AuditLog
from audit_logs.utils import log_audit_action

from .dashboard_config import get_user_dashboard_modules, get_user_dashboard_widgets

class DashboardIdentityView(APIView):
    """Returns the logged-in user's authorized modules and widgets based on RBAC."""
    # We allow any authenticated user to check their identity. 
    # If they have no permissions, they will simply get empty arrays.
    permission_classes = [] 

    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Unauthorized'}, status=403)
            
        user = request.user
        
        # Get modules and widgets from configuration
        modules = get_user_dashboard_modules(user)
        widgets = get_user_dashboard_widgets(user)
        
        # Collect explicit Django permissions for the frontend
        perms = list(user.get_all_permissions())
        
        # Collect groups to determine their specific team role
        groups = list(user.groups.values_list('name', flat=True))
        primary_group = groups[0] if groups else ('Administrator' if user.is_superuser else None)

        # Build user profile for the frontend
        user_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_supplier': getattr(user, 'is_supplier', False),
            'is_delivery': getattr(user, 'is_delivery', False),
            'is_customer': getattr(user, 'is_customer', False),
            'role_name': primary_group
        }
        
        return Response({
            'user': user_data,
            'permissions': perms,
            'modules': modules,
            'widgets': widgets,
            'environment': getattr(settings, 'ENVIRONMENT', 'production').capitalize()
        })

    def post(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Unauthorized'}, status=403)
            
        user = request.user
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                return Response({"message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.must_change_password = False
            user.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
            
        return Response({"message": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# Dashboard SPA File Serving
# =============================================================================

def dashboard_view(request, path='index.html'):
    """Serve the admin dashboard SPA files (HTML, CSS, JS)."""
    dashboard_dir = os.path.join(settings.BASE_DIR, 'dashboard')
    file_path = os.path.normpath(os.path.join(dashboard_dir, path))

    # Security: prevent directory traversal
    if not file_path.startswith(os.path.normpath(dashboard_dir)):
        raise Http404

    if not os.path.isfile(file_path):
        raise Http404

    content_types = {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.ico': 'image/x-icon',
        '.json': 'application/json',
        '.woff2': 'font/woff2',
        '.woff': 'font/woff',
    }
    ext = os.path.splitext(path)[1].lower()
    content_type = content_types.get(ext, 'application/octet-stream')

    if ext in ('.png', '.jpg', '.ico', '.woff2', '.woff'):
        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type=content_type)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type=content_type)


# =============================================================================
# KPI Stats & Chart Endpoints
# =============================================================================

class AdminStatsView(APIView):
    """Aggregated KPI statistics for the dashboard overview."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Revenue from succeeded payments
        succeeded_count = PaymentHistory.objects.filter(payment_status='succeeded').count()
        if succeeded_count > 0:
            order_revenue = PaymentHistory.objects.filter(
                payment_status='succeeded', order__isnull=False
            ).aggregate(total=Sum('order__final_amount'))['total'] or Decimal('0')
            course_revenue = PaymentHistory.objects.filter(
                payment_status='succeeded', course__isnull=False
            ).aggregate(total=Sum('course__Price'))['total'] or Decimal('0')
            total_revenue = order_revenue + course_revenue
        else:
            # Fallback: sum from product/course purchase transactions
            total_revenue = Transaction.objects.filter(
                transaction_type__in=[
                    Transaction.TransactionType.PURCHASED_PRODUCTS,
                    Transaction.TransactionType.PURCHASED_COURSE,
                ]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        from django.db.models import Q
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            total_orders = PaymentHistory.objects.filter(payment_status='succeeded', order__items__product__Supplier__user=request.user).distinct().count()
        else:
            total_orders = PaymentHistory.objects.filter(
                Q(order__isnull=False) | Q(course__isnull=False),
                payment_status='succeeded'
            ).distinct().count()
        active_users = User.objects.filter(is_active=True).count()
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            pending_returns = ReturnRequest.objects.filter(status='new', product__Supplier__user=request.user).count()
        else:
            pending_returns = ReturnRequest.objects.filter(status='new').count()
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            products_in_stock = Product.objects.filter(OutOfStock=False, Supplier__user=request.user).count()
        else:
            products_in_stock = Product.objects.filter(OutOfStock=False).count()
        pending_withdrawals = BalanceWithdrawRequest.objects.filter(
            transfer_status__in=['Requested', 'Awaiting Approval']
        ).count()

        # Revenue change
        last_month_start = (month_start - timezone.timedelta(days=1)).replace(day=1)
        this_month_qs = PaymentHistory.objects.filter(
            payment_status='succeeded',
            date__gte=month_start
        )
        last_month_qs = PaymentHistory.objects.filter(
            payment_status='succeeded',
            date__gte=last_month_start,
            date__lt=month_start
        )
        
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            this_month_qs = this_month_qs.filter(Q(order__items__product__Supplier__user=request.user) | Q(course__Supplier__user=request.user)).distinct()
            last_month_qs = last_month_qs.filter(Q(order__items__product__Supplier__user=request.user) | Q(course__Supplier__user=request.user)).distinct()
            
        this_month_revenue = this_month_qs.aggregate(total=Sum('order__final_amount'))['total'] or Decimal('0')
        last_month_revenue = last_month_qs.aggregate(total=Sum('order__final_amount'))['total'] or Decimal('0')
        
        revenue_change = 0
        if last_month_revenue > 0:
            revenue_change = round(((float(this_month_revenue) - float(last_month_revenue)) / float(last_month_revenue)) * 100, 1)
        elif this_month_revenue > 0:
            revenue_change = 100.0

        # Month-over-month order change
        this_month_orders_qs = Order.objects.filter(created_at__gte=month_start)
        last_month_orders_qs = Order.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=month_start
        )
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            this_month_orders_qs = this_month_orders_qs.filter(items__product__Supplier__user=request.user).distinct()
            last_month_orders_qs = last_month_orders_qs.filter(items__product__Supplier__user=request.user).distinct()
            
        this_month_orders = this_month_orders_qs.count()
        last_month_orders = last_month_orders_qs.count()
        orders_change = 0
        if last_month_orders > 0:
            orders_change = round(((this_month_orders - last_month_orders) / last_month_orders) * 100, 1)
        elif this_month_orders > 0:
            orders_change = 100.0

        # Avg Order Value
        avg_order_value = 0
        if total_orders > 0:
            avg_order_value = float(total_revenue) / total_orders

        # Conversion Rate (Orders / Total Users)
        total_users = User.objects.count()
        conversion_rate = 0
        if total_users > 0:
            conversion_rate = round((total_orders / total_users) * 100, 1)

        return Response({
            'total_revenue': float(total_revenue),
            'revenue_change': revenue_change,
            'total_orders': total_orders,
            'orders_change': orders_change,
            'active_users': active_users,
            'pending_returns': pending_returns,
            'products_in_stock': products_in_stock,
            'pending_withdrawals': pending_withdrawals,
            'avg_order_value': round(avg_order_value, 2),
            'conversion_rate': conversion_rate,
        })


class AdminChartsView(APIView):
    """Chart data for the dashboard overview."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        # Monthly revenue (last 6 months)
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        monthly_qs = PaymentHistory.objects.filter(
            payment_status='succeeded',
            date__gte=six_months_ago
        )
        
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            from django.db.models import Q
            monthly_qs = monthly_qs.filter(Q(order__items__product__Supplier__user=request.user) | Q(course__Supplier__user=request.user)).distinct()

        monthly = monthly_qs.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('order__final_amount')
        ).order_by('month')

        revenue_labels = [m['month'].strftime('%b') for m in monthly]
        revenue_data = [float(m['total'] or 0) for m in monthly]

        # Order status distribution
        statuses_qs = Order.objects.all()
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            statuses_qs = statuses_qs.filter(items__product__Supplier__user=request.user).distinct()
        elif not request.user.is_superuser and getattr(request.user, 'is_delivery', False):
            statuses_qs = statuses_qs.filter(shipments__delivery__user=request.user).distinct()
            
        statuses = statuses_qs.values('status').annotate(count=Count('id')).order_by('-count')
        status_labels = [s['status'].replace('_', ' ').title() for s in statuses]
        status_data = [s['count'] for s in statuses]

        return Response({
            'revenue_labels': revenue_labels or ['No Data'],
            'revenue_data': revenue_data or [0],
            'status_labels': status_labels or ['No Data'],
            'status_data': status_data or [0],
        })


class AdminSystemReportsView(APIView):
    """Generate system-wide financial and operational reports."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_view_financial_reports')]

    def get(self, request):
        period = request.query_params.get('period', 'this_month')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        now = timezone.now()

        if period == 'custom' and start_date and end_date:
            try:
                start_dt = timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                end_dt = timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                current_start = start_dt
                current_end = end_dt
                # rough approx for prior period comparison
                delta = current_end - current_start
                prev_start = current_start - delta
                prev_end = current_start
            except ValueError:
                from reports.services import get_date_range_for_period
                current_start, current_end, prev_start, prev_end = get_date_range_for_period(period_string='this_month')
        else:
            from reports.services import get_date_range_for_period
            try:
                current_start, current_end, prev_start, prev_end = get_date_range_for_period(period_string=period)
            except Exception:
                return Response({"error": _("Invalid period")}, status=status.HTTP_400_BAD_REQUEST)

        income_types = [
            Transaction.TransactionType.PURCHASED_PRODUCTS,
            Transaction.TransactionType.PURCHASED_COURSE
        ]
        outcome_types = [
            Transaction.TransactionType.WITHDRAWAL_REQUEST,
            Transaction.TransactionType.RETURN_DEBIT,
            Transaction.TransactionType.REFUND_FAILED
        ]

        transactions = Transaction.objects.filter(
            created_at__date__gte=current_start,
            created_at__date__lte=current_end
        )

        graph_data = transactions.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            income=Sum('amount', filter=Q(transaction_type__in=income_types)),
            outcome=Sum('amount', filter=Q(transaction_type__in=outcome_types))
        ).order_by('month')

        formatted_graph_data = [
            {
                "month": item['month'].strftime("%b") if item['month'] else "Unknown",
                "income": float(item['income'] or 0),
                "outcome": float(abs(item['outcome'] or 0))
            }
            for item in graph_data
        ]

        current_totals = transactions.aggregate(
            total_income=Sum('amount', filter=Q(transaction_type__in=income_types)),
            total_outcome=Sum('amount', filter=Q(transaction_type__in=outcome_types))
        )
        current_total_income = current_totals.get('total_income') or Decimal('0.0')
        current_total_outcome = current_totals.get('total_outcome') or Decimal('0.0')
        current_earning = current_total_income + current_total_outcome

        prev_totals = Transaction.objects.filter(
            created_at__date__gte=prev_start,
            created_at__date__lte=prev_end
        ).aggregate(
            total_income=Sum('amount', filter=Q(transaction_type__in=income_types)),
            total_outcome=Sum('amount', filter=Q(transaction_type__in=outcome_types))
        )
        prev_total_income = prev_totals.get('total_income') or Decimal('0.0')
        prev_total_outcome = prev_totals.get('total_outcome') or Decimal('0.0')
        previous_earning = prev_total_income + prev_total_outcome

        percentage_change = 0.0
        if previous_earning > 0:
            percentage_change = float(((current_earning - previous_earning) / previous_earning) * 100)
        elif current_earning > 0:
            percentage_change = 100.0

        # Payment Method Breakdown
        payment_methods = Order.objects.filter(
            created_at__gte=current_start,
            created_at__lte=current_end,
            paid=True
        ).values('payment_method').annotate(total=Sum('final_amount')).order_by('-total')
        
        pm_labels = [p['payment_method'] for p in payment_methods]
        pm_data = [float(p['total'] or 0) for p in payment_methods]

        # Quick Stats
        total_customers = User.objects.filter(is_customer=True).count()
        total_products = Product.objects.count()
        avg_rating = Product.objects.aggregate(avg=Avg('Rating'))['avg'] or 0

        return Response({
            'total_income': float(current_total_income),
            'total_outcome': float(abs(current_total_outcome)),
            'total_earning': float(current_earning),
            'percentage_change': round(percentage_change, 2),
            'graph_data': formatted_graph_data,
            'payment_methods': {
                'labels': pm_labels if pm_labels else ['No Data'],
                'data': pm_data if pm_data else [1]
            },
            'quick_stats': {
                'customers': total_customers,
                'products': total_products,
                'avg_rating': round(float(avg_rating), 1)
            }
        })



# =============================================================================
# Admin List Endpoints — Full data access for all entities
# =============================================================================

class AdminOrdersView(APIView):
    """List all orders (optionally filtered by date)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        orders = Order.objects.select_related('user').all()
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            orders = orders.filter(created_at__date__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__date__lte=end_date)
            
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            orders = orders.filter(items__product__Supplier__user=request.user).distinct()
        elif not request.user.is_superuser and getattr(request.user, 'is_delivery', False):
            orders = orders.filter(shipments__delivery__user=request.user).distinct()
            
        orders = orders.select_related('user', 'address').prefetch_related('items__product').order_by('-created_at')[:200]
        data = [{
            'id': str(o.id),
            'order_number': o.order_number,
            'user_email': o.user.email,
            'total_amount': float(o.total_amount),
            'discount_amount': float(o.discount_amount),
            'delivery_fee': float(o.delivery_fee),
            'final_amount': float(o.final_amount),
            'payment_method': o.payment_method,
            'status': o.status,
            'paid': o.paid,
            'created_at': o.created_at.isoformat(),
            'items': [{
                'product_name': item.product.ProductName,
                'quantity': item.quantity,
                'price': float(item.price),
            } for item in o.items.all()],
        } for o in orders]
        return Response(data)


class AdminProductsView(APIView):
    """List all products for admin dashboard."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        products = Product.objects.select_related('Supplier__user').prefetch_related('images').all()
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            products = products.filter(Supplier__user=request.user)
        products = products[:500]
        data = [{
            'id': p.id,
            'ProductName': p.__dict__.get('ProductName_en') or p.__dict__.get('ProductName_ar') or p.__dict__.get('ProductName') or getattr(p, 'ProductName', ''),
            'UnitPrice': float(p.UnitPrice),
            'Stock': p.Stock,
            'OutOfStock': p.OutOfStock,
            'Rating': float(p.Rating),
            'NumberOfRatings': p.NumberOfRatings if hasattr(p, 'NumberOfRatings') else 0,
            'DiscountPercentage': float(p.DiscountPercentage) if p.DiscountPercentage else 0,
            'supplier_name': f"{p.Supplier.user.first_name} {p.Supplier.user.last_name}" if p.Supplier else '',
            'images': [{'image': img.image.url if img.image else ''} for img in p.images.all()[:3]],
        } for p in products]
        return Response(data)


class AdminReturnsView(APIView):
    """List all return requests."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        returns = ReturnRequest.objects.select_related('product', 'order__user').all()
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            returns = returns.filter(product__Supplier__user=request.user)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            returns = returns.filter(created_at__date__gte=start_date)
        if end_date:
            returns = returns.filter(created_at__date__lte=end_date)
            
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            returns = returns.filter(order__items__product__Supplier__user=request.user).distinct()
            
        returns = returns.order_by('-created_at')[:300]
        data = [{
            'id': str(r.id),
            'product_name': r.product.ProductName if r.product else '',
            'customer_name': f"{r.user.first_name} {r.user.last_name}" if r.user else '',
            'quantity': r.quantity,
            'amount': float(r.amount) if r.amount else 0,
            'reason': r.reason,
            'status': r.status,
            'image': r.image.url if r.image else None,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        } for r in returns]
        return Response(data)


class AdminCoursesView(APIView):
    """List all courses for admin dashboard."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        courses = Course.objects.select_related(
            'Supplier__user', 'CategoryID'
        ).annotate(
            enrollment_count=Count('enrollments')
        ).all()
        
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            courses = courses.filter(Supplier__user=request.user)
        data = [{
            'CourseID': c.CourseID,
            'CourseTitle': c.__dict__.get('CourseTitle_en') or c.__dict__.get('CourseTitle_ar') or c.__dict__.get('CourseTitle') or getattr(c, 'CourseTitle', ''),
            'Price': float(c.Price),
            'Rating': float(c.Rating),
            'NumberOfRatings': c.NumberOfRatings,
            'Thumbnail': c.Thumbnail.url if c.Thumbnail else None,
            'supplier_name': f"{c.Supplier.user.first_name} {c.Supplier.user.last_name}" if c.Supplier else '',
            'enrollments_count': c.enrollment_count,
            'completed': c.completed,
            'CourseHours': c.CourseHours,
            'NumberOfLec': c.NumberOfLec,
        } for c in courses]
        return Response(data)


class AdminReviewsView(APIView):
    """List all reviews for admin dashboard."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        reviews = Review.objects.select_related('customer__user', 'product', 'course').all()
        
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            reviews = reviews.filter(product__Supplier__user=request.user)
            
        reviews = reviews.order_by('-created_at')[:300]
        data = [{
            'id': r.id,
            'customer_name': f"{r.customer.user.first_name} {r.customer.user.last_name}" if r.customer else '',
            'product_name': r.product.ProductName if r.product else '',
            'course_name': r.course.CourseTitle if r.course else '',
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        } for r in reviews]
        return Response(data)


class AdminCouponsView(APIView):
    """List all coupons for admin dashboard."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        coupons = Coupon.objects.select_related('supplier__user').all()
        
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            coupons = coupons.filter(supplier__user=request.user)
        data = [{
            'id': c.id,
            'code': c.code,
            'supplier_name': f"{c.supplier.user.first_name} {c.supplier.user.last_name}" if c.supplier else '',
            'discount': float(c.discount),
            'discount_type': c.discount_type,
            'active': c.active and (c.valid_to >= timezone.now() if c.valid_to else True),
            'valid_from': c.valid_from.isoformat() if c.valid_from else None,
            'valid_to': c.valid_to.isoformat() if c.valid_to else None,
            'max_uses': c.max_uses,
            'uses_count': c.uses_count,
            'min_purchase_amount': float(c.min_purchase_amount),
        } for c in coupons]
        return Response(data)


class AdminTransactionsView(APIView):
    """List all transactions for admin dashboard."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        txns = Transaction.objects.select_related('user').all()
        
        if not request.user.is_superuser:
            txns = txns.filter(user=request.user)
            
        txns = txns.order_by('-created_at')[:300]
        data = [{
            'id': str(t.id),
            'user_email': t.user.email if t.user else '',
            'transaction_type': t.transaction_type,
            'amount': float(t.amount),
            'created_at': t.created_at.isoformat() if t.created_at else None,
        } for t in txns]
        return Response(data)


class AdminWithdrawalsListView(APIView):
    """List all withdrawal requests for admin dashboard."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        withdrawals = BalanceWithdrawRequest.objects.select_related('user').all()
        
        if not request.user.is_superuser:
            withdrawals = withdrawals.filter(user=request.user)
            
        withdrawals = withdrawals.order_by('-created_at')[:300]
        data = [{
            'id': str(w.id),
            'user_name': f"{w.user.first_name} {w.user.last_name}" if w.user else '',
            'amount': float(w.amount),
            'transfer_type': w.transfer_type,
            'transfer_number': w.transfer_number,
            'transfer_status': w.transfer_status,
            'risk_score': float(w.risk_score) if hasattr(w, 'risk_score') and w.risk_score else 0,
            'notes': w.notes if hasattr(w, 'notes') else '',
            'admin_notes': w.admin_notes if hasattr(w, 'admin_notes') else '',
            'created_at': w.created_at.isoformat() if w.created_at else None,
        } for w in withdrawals]
        return Response(data)


class AdminNotificationsView(APIView):
    """List all notifications (system-wide) for admin dashboard."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        notifs = Notification.objects.select_related('user').order_by('-timestamp')[:200]
        data = [{
            'id': n.id,
            'user_email': n.user.email if n.user else '',
            'message': n.message,
            'is_read': n.is_read,
            'timestamp': n.timestamp.isoformat() if n.timestamp else None,
        } for n in notifs]
        return Response(data)

    def post(self, request):
        """Mark all notifications as read."""
        Notification.objects.filter(is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})


# =============================================================================
# User Management Endpoints
# =============================================================================

class AdminUsersView(APIView):
    """List all users grouped by role."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_suspend_users')]

    def get(self, request):
        customers_qs = User.objects.filter(is_customer=True).values(
            'id', 'email', 'first_name', 'last_name', 'PhoneNO',
            'is_verified', 'Balance', 'date_joined', 'is_active'
        )
        customers = [
            {**c, 'date_joined': c['date_joined'].isoformat() if c['date_joined'] else None}
            for c in customers_qs
        ]
        suppliers_qs = Supplier.objects.select_related('user').all()
        suppliers = [{
            'id': s.id,
            'user_id': s.user_id,
            'name': f"{s.user.first_name} {s.user.last_name}",
            'email': s.user.email,
            'CategoryTitle': s.CategoryTitle,
            'Rating': float(s.Rating),
            'FollowersNo': s.FollowersNo,
            'Orders': s.Orders,
            'ExperienceYears': s.ExperienceYears,
            'accepted_supplier': s.accepted_supplier,
        } for s in suppliers_qs]

        delivery_qs = Delivery.objects.select_related('user').all()
        delivery = [{
            'id': d.id,
            'user_id': d.user_id,
            'name': f"{d.user.first_name} {d.user.last_name}",
            'email': d.user.email,
            'VehicleModel': d.VehicleModel,
            'VehicleColor': d.VehicleColor,
            'plateNO': d.plateNO,
            'governorate': d.governorate,
            'Rating': float(d.Rating),
            'Orders': d.Orders,
            'accepted_delivery': d.accepted_delivery,
        } for d in delivery_qs]

        return Response({
            'customers': list(customers),
            'suppliers': suppliers,
            'delivery': delivery,
        })


class AdminUserToggleView(APIView):
    """Activate or deactivate a user."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_suspend_users')]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': _('User not found')}, status=status.HTTP_404_NOT_FOUND)

        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
            user.save(update_fields=['is_active'])
            
            action = "Admin activated user" if user.is_active else "Admin suspended user"
            log_audit_action(
                user=request.user,
                action=action,
                instance=user,
                new_value={'is_active': user.is_active},
                request=request
            )
            
        return Response({'status': 'updated', 'is_active': user.is_active})


# =============================================================================
# Admin Action Endpoints
# =============================================================================

class AdminSupplierApprovalView(APIView):
    """Approve or update a supplier."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_verify_suppliers')]

    def patch(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
        except Supplier.DoesNotExist:
            return Response({'error': _('Supplier not found')}, status=status.HTTP_404_NOT_FOUND)

        if 'accepted_supplier' in request.data:
            supplier.accepted_supplier = request.data['accepted_supplier']
            supplier.save(update_fields=['accepted_supplier'])
            
            action = "Admin approved supplier" if supplier.accepted_supplier else "Admin revoked supplier approval"
            log_audit_action(
                user=request.user,
                action=action,
                instance=supplier,
                new_value={'accepted_supplier': supplier.accepted_supplier},
                request=request
            )
            
        return Response({'status': 'updated'})

    def delete(self, request, pk):
        try:
            supplier = Supplier.objects.get(pk=pk)
            user = supplier.user
            
            log_audit_action(
                user=request.user,
                action="Admin denied and deleted supplier application",
                instance=supplier,
                new_value=None,
                request=request
            )
            user.delete()
            return Response({'status': 'deleted'})
        except Supplier.DoesNotExist:
            return Response({'error': _('Supplier not found')}, status=status.HTTP_404_NOT_FOUND)


class AdminDeliveryApprovalView(APIView):
    """Approve or update a delivery person."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_verify_suppliers')]

    def patch(self, request, pk):
        try:
            delivery = Delivery.objects.get(pk=pk)
        except Delivery.DoesNotExist:
            return Response({'error': _('Delivery person not found')}, status=status.HTTP_404_NOT_FOUND)

        if 'accepted_delivery' in request.data:
            delivery.accepted_delivery = request.data['accepted_delivery']
            delivery.save(update_fields=['accepted_delivery'])
            
            action = "Admin approved delivery" if delivery.accepted_delivery else "Admin revoked delivery approval"
            log_audit_action(
                user=request.user,
                action=action,
                instance=delivery,
                new_value={'accepted_delivery': delivery.accepted_delivery},
                request=request
            )
            
        return Response({'status': 'updated'})

    def delete(self, request, pk):
        try:
            delivery = Delivery.objects.get(pk=pk)
            user = delivery.user
            
            log_audit_action(
                user=request.user,
                action="Admin denied and deleted delivery application",
                instance=delivery,
                new_value=None,
                request=request
            )
            user.delete()
            return Response({'status': 'deleted'})
        except Delivery.DoesNotExist:
            return Response({'error': _('Delivery person not found')}, status=status.HTTP_404_NOT_FOUND)


class AdminReturnActionView(APIView):
    """Accept, reject, or cancel a return request."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_refund_orders')]

    def post(self, request, pk):
        try:
            ret = ReturnRequest.objects.get(pk=pk)
        except ReturnRequest.DoesNotExist:
            return Response({'error': _('Return request not found')}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'accept':
            ret.approve_by_supplier()
        elif action == 'reject':
            ret.reject_by_supplier()
        elif action == 'cancel':
            ret.cancel()
        else:
            return Response({'error': _('Invalid action')}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': _('Return {action}ed').format(action=action), 'new_status': ret.status})


class AdminWithdrawalActionView(APIView):
    """Approve or reject a withdrawal request."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_approve_withdrawals')]

    def post(self, request, pk):
        try:
            wd = BalanceWithdrawRequest.objects.get(pk=pk)
        except BalanceWithdrawRequest.DoesNotExist:
            return Response({'error': _('Withdrawal not found')}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'approve':
            wd.transfer_status = 'Approved'
        elif action == 'reject':
            wd.transfer_status = 'Rejected'
        elif action == 'complete':
            wd.transfer_status = 'Completed'
        else:
            return Response({'error': _('Invalid action')}, status=status.HTTP_400_BAD_REQUEST)

        if request.data.get('admin_notes'):
            wd.admin_notes = request.data['admin_notes']

        wd.save()
        return Response({'status': _('Withdrawal {action}d').format(action=action), 'new_status': wd.transfer_status})


class AdminReviewModerationView(APIView):
    """Approve or reject a review."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_moderate_reviews')]

    def patch(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response({'error': _('Review not found')}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in [Review.Status.APPROVED, Review.Status.REJECTED]:
            return Response({'error': _('Invalid status')}, status=status.HTTP_400_BAD_REQUEST)

        review.status = new_status
        review.save(update_fields=['status'])
        
        return Response({'status': _('Review updated successfully'), 'new_status': review.status})


class AdminPaymentsView(APIView):
    """List all payment history records."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        payments = PaymentHistory.objects.select_related('user', 'order', 'course').order_by('-date')[:200]
        data = [{
            'id': str(p.id),
            'user_email': p.user.email if p.user else None,
            'order_id': str(p.order_id) if p.order_id else None,
            'course_id': p.course_id,
            'payment_status': p.payment_status,
            'stripe_session_id': p.stripe_session_id,
            'stripe_payment_intent_id': p.stripe_payment_intent_id,
            'date': p.date.isoformat() if p.date else None,
        } for p in payments]
        return Response(data)


class AdminOrderStatusView(APIView):
    """Update order status."""
    permission_classes = [IsDashboardUser]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': _('Order not found')}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status:
            order.status = new_status
            order.save(update_fields=['status'])
        return Response({'status': 'updated', 'new_status': order.status})

class AdminSystemHealthView(APIView):
    """Return system health (DB, Cache)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        health = {
            "database": "down",
            "redis": "down"
        }
        
        # Check DB
        try:
            from django.db import connection
            connection.cursor()
            health["database"] = "up"
        except Exception:
            pass
            
        # Check Redis
        try:
            import redis
            from django.conf import settings
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            health["redis"] = "up"
        except Exception:
            pass
            
        return Response(health)

class AdminTopProductsView(APIView):
    """Return top 5 selling products."""
    permission_classes = [IsDashboardUser]

    @method_decorator(cache_page(60 * 5))
    def get(self, request):
        from django.db.models import Sum, F
        from django.utils.translation import get_language
        lang = get_language()

        # Calculate top products by total quantity sold in successful orders
        top_items = OrderItem.objects.filter(
            order__paymenthistory__payment_status='succeeded'
        ).values(
            'product__id', 
            'product__ProductName', 
            'product__ProductName_ar',
            'product__Category__Title',
            'product__Category__Title_ar',
            'product__UnitPrice'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-total_sold')[:5]

        data = []
        for item in top_items:
            name = item.get('product__ProductName_ar') if lang == 'ar' and item.get('product__ProductName_ar') else item['product__ProductName']
            cat = item.get('product__Category__Title_ar') if lang == 'ar' and item.get('product__Category__Title_ar') else item['product__Category__Title']
            
            data.append({
                'id': item['product__id'],
                'name': name,
                'category': cat,
                'price': float(item['product__UnitPrice'] or 0),
                'total_sold': item['total_sold'],
                'total_revenue': float(item['total_revenue'] or 0)
            })

        return Response(data)

class AdminRecentActivityView(APIView):
    """Return 10 most recent audit logs."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_view_audit_logs')]

    def get(self, request):
        from audit_logs.models import AuditLog
        logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'action': log.action,
                'actor': log.user.email if log.user else 'System',
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address
            })
        return Response(data)

class AdminSupportTicketsView(APIView):
    """List recent support tickets."""
    permission_classes = [IsDashboardUser]
    
    def get(self, request):
        from support_tickets.models import Ticket
        tickets = Ticket.objects.select_related('user').order_by('-created_at')[:100]
        data = []
        for t in tickets:
            data.append({
                'id': t.id,
                'user_email': t.user.email if t.user else '',
                'subject': t.subject,
                'status': t.status,
                'priority': t.priority,
                'created_at': t.created_at.isoformat(),
            })
        return Response(data)

class AdminDisputesView(APIView):
    """List recent disputes."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from disputes.models import Dispute
        disputes = Dispute.objects.select_related('customer', 'supplier', 'order').order_by('-created_at')[:100]
        data = []
        for d in disputes:
            data.append({
                'id': d.id,
                'customer_email': d.customer.email if d.customer else '',
                'supplier_email': d.supplier.email if d.supplier else '',
                'order_number': d.order.order_number if d.order else '',
                'status': d.status,
                'reason': d.reason,
                'created_at': d.created_at.isoformat(),
            })
        return Response(data)

class AdminGlobalSearchView(APIView):
    """Global search across Orders, Users, and Products."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({"results": []})
            
        import concurrent.futures
        from django.db.models import Q, Value
        from django.db.models.functions import Concat
        
        def fetch_orders():
            from orders.models import Order
            orders = Order.objects.annotate(
                user_full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            ).filter(
                Q(order_number__icontains=query) |
                Q(user__email__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user_full_name__icontains=query)
            ).select_related('user')[:5]
            return [{
                'type': 'order',
                'id': str(o.id),
                'title': f"Order #{o.order_number}",
                'subtitle': o.user.email if o.user else 'No user',
                'url': '#orders'
            } for o in orders]

        def fetch_customers():
            from accounts.models import User
            customers = User.objects.filter(is_customer=True).annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(full_name__icontains=query) |
                Q(PhoneNO__icontains=query)
            )[:5]
            return [{
                'type': 'customer',
                'id': str(c.id),
                'title': getattr(c, 'get_full_name', getattr(c, 'first_name', '')),
                'subtitle': f"Customer - {c.email}",
                'url': '#users'
            } for c in customers]

        def fetch_suppliers():
            from accounts.models import Supplier
            suppliers = Supplier.objects.select_related('user').annotate(
                user_full_name=Concat('user__first_name', Value(' '), 'user__last_name')
            ).filter(
                Q(user__email__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user_full_name__icontains=query) |
                Q(user__PhoneNO__icontains=query) |
                Q(CategoryTitle__icontains=query)
            )[:5]
            return [{
                'type': 'supplier',
                'id': str(s.id),
                'title': getattr(s.user, 'get_full_name', getattr(s.user, 'first_name', '')),
                'subtitle': f"Supplier ({s.CategoryTitle}) - {s.user.email}",
                'url': '#users'
            } for s in suppliers]

        def fetch_products():
            from products.models import Product
            products = Product.objects.filter(ProductName__icontains=query)[:5]
            return [{
                'type': 'product',
                'id': str(p.id),
                'title': p.ProductName,
                'subtitle': f"EGP {p.UnitPrice}",
                'url': '#products'
            } for p in products]

        def fetch_courses():
            from course.models import Course
            courses = Course.objects.filter(
                Q(CourseTitle__icontains=query) | Q(Description__icontains=query)
            ).select_related('Supplier__user')[:5]
            return [{
                'type': 'course',
                'id': str(c.CourseID),
                'title': c.CourseTitle,
                'subtitle': f"Course by {c.Supplier.user.get_full_name if c.Supplier and c.Supplier.user else 'Unknown'}",
                'url': '#courses'
            } for c in courses]

        def fetch_tickets():
            from support_tickets.models import Ticket
            tickets = Ticket.objects.filter(
                Q(subject__icontains=query) | Q(user_email__icontains=query) | Q(description__icontains=query)
            )[:5]
            return [{
                'type': 'ticket',
                'id': str(t.id),
                'title': f"Ticket #{t.id}: {t.subject}",
                'subtitle': t.user_email,
                'url': '#support-tickets'
            } for t in tickets]

        def fetch_disputes():
            from disputes.models import Dispute
            disputes = Dispute.objects.filter(
                Q(reason__icontains=query) | Q(customer_email__icontains=query) |
                Q(supplier_email__icontains=query) | Q(order__order_number__icontains=query)
            )[:5]
            return [{
                'type': 'dispute',
                'id': str(d.id),
                'title': f"Dispute #{d.id}",
                'subtitle': d.reason[:30] + ('...' if len(d.reason) > 30 else ''),
                'url': '#disputes'
            } for d in disputes]

        def fetch_reviews():
            from reviews.models import Review
            reviews = Review.objects.filter(comment__icontains=query)[:5]
            return [{
                'type': 'review',
                'id': str(r.id),
                'title': f"Review ({r.rating} stars)",
                'subtitle': r.comment[:30] + ('...' if len(r.comment) > 30 else ''),
                'url': '#reviews'
            } for r in reviews]

        def fetch_coupons():
            from orders.models import Coupon
            coupons = Coupon.objects.filter(code__icontains=query)[:5]
            return [{
                'type': 'coupon',
                'id': str(c.id),
                'title': c.code,
                'subtitle': f"{c.discount_percentage}% off",
                'url': '#coupons'
            } for c in coupons]

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
            futures = [
                executor.submit(fetch_orders),
                executor.submit(fetch_customers),
                executor.submit(fetch_suppliers),
                executor.submit(fetch_products),
                executor.submit(fetch_courses),
                executor.submit(fetch_tickets),
                executor.submit(fetch_disputes),
                executor.submit(fetch_reviews),
                executor.submit(fetch_coupons)
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.extend(future.result())
                except Exception as e:
                    pass  # Ignore failing queries to ensure smooth search experience
                    
        return Response({"results": results})

class AdminSendNotificationView(APIView):
    """Send a custom notification to a specific user or all users."""
    permission_classes = [IsDashboardUser]

    def post(self, request):
        from notifications.models import Notification
        from accounts.models import User
        
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('type', 'system')
        
        if not title or not message:
            return Response({"error": "Title and message are required"}, status=400)
            
        if user_id and str(user_id).lower() != 'all':
            try:
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type
                )
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)
        else:
            # Send to all active users
            users = User.objects.filter(is_active=True)
            notifications = [
                Notification(
                    user=u,
                    title=title,
                    message=message,
                    notification_type=notification_type
                ) for u in users
            ]
            Notification.objects.bulk_create(notifications)
            
        return Response({"status": "success", "message": "Notification sent successfully"})

class AdminUserDetailView(APIView):
    """Get detailed information about a specific user."""
    permission_classes = [IsDashboardUser]

    def get(self, request, pk):
        from accounts.models import User
        from django.shortcuts import get_object_or_404
        
        user = get_object_or_404(User, pk=pk)
        data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name,
            'phone': user.PhoneNO,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'balance': float(user.Balance) if user.Balance else 0,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'type': 'customer'
        }
        
        if hasattr(user, 'supplier'):
            data['type'] = 'supplier'
            data['supplier_info'] = {
                'category': user.supplier.CategoryTitle,
                'rating': float(user.supplier.Rating),
                'orders': user.supplier.Orders,
                'followers': user.supplier.FollowersNo,
                'accepted': user.supplier.accepted_supplier,
                'contract_url': request.build_absolute_uri(user.supplier.SupplierContract.url) if user.supplier.SupplierContract and user.supplier.SupplierContract.name else None,
                'identity_url': request.build_absolute_uri(user.supplier.SupplierIdentity.url) if user.supplier.SupplierIdentity and user.supplier.SupplierIdentity.name else None,
            }
        elif hasattr(user, 'delivery'):
            data['type'] = 'delivery'
            data['delivery_info'] = {
                'vehicle': user.delivery.VehicleModel,
                'plate': user.delivery.plateNO,
                'area': user.delivery.governorate,
                'rating': float(user.delivery.Rating),
                'accepted': user.delivery.accepted_delivery,
                'contract_url': request.build_absolute_uri(user.delivery.DeliveryContract.url) if user.delivery.DeliveryContract and user.delivery.DeliveryContract.name else None,
                'identity_url': request.build_absolute_uri(user.delivery.DeliveryIdentity.url) if user.delivery.DeliveryIdentity and user.delivery.DeliveryIdentity.name else None,
            }
            
        return Response(data)

# =============================================================================
# Operational Performance Endpoints
# =============================================================================

class AdminSupplierPerformanceView(APIView):
    """Calculates operational performance scores for suppliers."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        suppliers = Supplier.objects.select_related('user').all()
        data = []
        for s in suppliers:
            from orders.models import Order
            total_orders = Order.objects.filter(items__product__Supplier=s).distinct().count()
            returns_count = s.return_requests.count()
            
            return_rate = (returns_count / total_orders * 100) if total_orders > 0 else 0.0
            success_rate = 100.0 - return_rate

            rating = float(getattr(s, 'Rating', 0))
            score = (rating * 10) + (success_rate * 0.5)

            status_label = 'Excellent' if score >= 85 else 'Warning' if score >= 60 else 'High Risk'
            if total_orders < 5:
                status_label = 'New'

            data.append({
                'id': s.id,
                'supplier_name': s.user.get_full_name if s.user else "Unknown",
                'email': s.user.email if s.user else "Unknown",
                'category': s.CategoryTitle,
                'total_orders': total_orders,
                'returns_count': returns_count,
                'return_rate': round(return_rate, 1),
                'success_rate': round(success_rate, 1),
                'rating': round(rating, 1),
                'performance_score': round(score, 1),
                'status': status_label
            })
        
        data.sort(key=lambda x: x['performance_score'], reverse=True)
        return Response(data)


class AdminDeliveryPerformanceView(APIView):
    """Calculates operational performance scores for delivery agents."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        deliveries = Delivery.objects.select_related('user').all()
        from orders.models import Shipment
        data = []
        for d in deliveries:
            total_assigned = Shipment.objects.filter(delivery_person=d).count()
            success_count = Shipment.objects.filter(delivery_person=d, status=Shipment.ShipmentStatus.DELIVERED_SUCCESSFULLY).count()
            failed_count = Shipment.objects.filter(delivery_person=d, status=Shipment.ShipmentStatus.FAILED_DELIVERY).count()
            
            success_rate = (success_count / total_assigned * 100) if total_assigned > 0 else 0.0
            
            rating = float(getattr(d, 'Rating', 0))
            score = (rating * 10) + (success_rate * 0.5)
            
            status_label = 'Excellent' if score >= 85 else 'Warning' if score >= 60 else 'High Risk'
            if total_assigned < 10:
                status_label = 'New'

            data.append({
                'id': d.id,
                'delivery_name': d.user.get_full_name if d.user else "Unknown",
                'email': d.user.email if d.user else "Unknown",
                'area': d.governorate,
                'total_assigned': total_assigned,
                'success_count': success_count,
                'failed_count': failed_count,
                'success_rate': round(success_rate, 1),
                'rating': round(rating, 1),
                'performance_score': round(score, 1),
                'status': status_label
            })

        data.sort(key=lambda x: x['performance_score'], reverse=True)
        return Response(data)

class AdminFinancialReconciliationView(APIView):
    """Aggregate financial ledger for identifying discrepancies between Stripe, internal income, and balances."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from payment.models import PaymentHistory
        from orders.models import Order
        from accounts.models import User
        from returnrequest.models import Transaction, BalanceWithdrawRequest
        from decimal import Decimal

        stripe_orders = PaymentHistory.objects.filter(payment_status='succeeded', order__isnull=False).aggregate(total=Sum('order__final_amount'))['total'] or Decimal('0.0')
        stripe_courses = PaymentHistory.objects.filter(payment_status='succeeded', course__isnull=False).aggregate(total=Sum('course__Price'))['total'] or Decimal('0.0')
        total_stripe_captured = float(stripe_orders) + float(stripe_courses)

        order_val = Order.objects.filter(paid=True).aggregate(total=Sum('final_amount'))['total'] or Decimal('0.0')
        from course.models import Enrollment
        enrollment_val = Enrollment.objects.aggregate(total=Sum('Course__Price'))['total'] or Decimal('0.0')
        total_order_value = float(order_val) + float(enrollment_val)

        total_balances = User.objects.aggregate(total=Sum('Balance'))['total'] or Decimal('0.0')

        income_types = [
            Transaction.TransactionType.PURCHASED_PRODUCTS,
            Transaction.TransactionType.PURCHASED_COURSE
        ]
        outcome_types = [
            Transaction.TransactionType.WITHDRAWAL_REQUEST,
            Transaction.TransactionType.RETURN_DEBIT,
            Transaction.TransactionType.REFUND_FAILED
        ]
        total_income = Transaction.objects.filter(transaction_type__in=income_types).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
        total_outcome = Transaction.objects.filter(transaction_type__in=outcome_types).aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
        
        total_withdrawals = BalanceWithdrawRequest.objects.filter(transfer_status='Completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.0')

        internal_discrepancy = float(total_income) - abs(float(total_outcome)) - float(total_balances)
        stripe_discrepancy = float(total_stripe_captured) - float(total_income)

        status_flag = "Healthy"
        if abs(internal_discrepancy) > 1.0 or abs(stripe_discrepancy) > 1.0:
            status_flag = "Discrepancy Detected"

        return Response({
            "total_stripe_captured": total_stripe_captured,
            "total_order_value": float(total_order_value),
            "total_internal_income": float(total_income),
            "total_internal_outcome": float(abs(total_outcome)),
            "total_user_balances": float(total_balances),
            "total_withdrawals": float(total_withdrawals),
            "internal_discrepancy": round(internal_discrepancy, 2),
            "stripe_discrepancy": round(stripe_discrepancy, 2),
            "status": status_flag
        })

class AdminFraudAlertsView(APIView):
    """View and manage fraud alerts."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_view_audit_logs')]

    def get(self, request):
        from audit_logs.models import FraudAlert
        alerts = FraudAlert.objects.select_related('user').order_by('-created_at')[:200]
        data = [{
            'id': a.id,
            'user_email': a.user.email if a.user else 'Unknown',
            'user_id': a.user.id if a.user else None,
            'reason': a.reason,
            'risk_score': a.risk_score,
            'status': a.status,
            'created_at': a.created_at.isoformat() if a.created_at else None,
        } for a in alerts]
        return Response(data)

class AdminFraudAlertActionView(APIView):
    """Resolve or take action on a fraud alert."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_suspend_users')]
    
    def post(self, request, pk):
        from audit_logs.models import FraudAlert
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        
        alert = get_object_or_404(FraudAlert, pk=pk)
        action = request.data.get('action')
        
        if action == 'resolve':
            alert.status = FraudAlert.Status.RESOLVED
            alert.resolved_at = timezone.now()
            alert.resolved_by = request.user
            if request.data.get('notes'):
                alert.notes = request.data['notes']
            alert.save()
            return Response({'status': 'resolved'})
        elif action == 'suspend_user':
            alert.status = FraudAlert.Status.ACTION_TAKEN
            alert.resolved_at = timezone.now()
            alert.resolved_by = request.user
            alert.save()
            
            if alert.user:
                alert.user.is_active = False
                alert.user.save(update_fields=['is_active'])
            return Response({'status': 'user suspended'})
        
        return Response({'error': 'Invalid action'}, status=400)

class AdminProductModerationView(APIView):
    """List products pending moderation."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from products.models import Product
        products = Product.objects.select_related('Supplier__user').filter(publish_status=Product.PublishStatus.PENDING)
        data = [{
            'id': p.id,
            'ProductName': p.ProductName,
            'Supplier': p.Supplier.user.email if p.Supplier and p.Supplier.user else 'Unknown',
            'UnitPrice': float(p.UnitPrice),
            'Publish_Date': p.Publish_Date.isoformat() if p.Publish_Date else None,
        } for p in products]
        return Response(data)

class AdminProductModerationActionView(APIView):
    """Approve or reject product."""
    permission_classes = [IsDashboardUser]
    
    def post(self, request, pk):
        from products.models import Product
        from django.shortcuts import get_object_or_404
        
        product = get_object_or_404(Product, pk=pk)
        action = request.data.get('action')
        
        if action == 'approve':
            product.publish_status = Product.PublishStatus.APPROVED
            product.save(update_fields=['publish_status'])
            return Response({'status': 'approved'})
        elif action == 'reject':
            product.publish_status = Product.PublishStatus.REJECTED
            product.save(update_fields=['publish_status'])
            return Response({'status': 'rejected'})
            
        return Response({'error': 'Invalid action'}, status=400)

class AdminAuditLogsView(APIView):
    """View system audit logs (Admin operations, user changes, etc.)"""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_view_audit_logs')]

    def get(self, request):
        logs = AuditLog.objects.select_related('user').all()[:200]
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'user': log.user.email if log.user else 'System',
                'action': log.action,
                'model': log.entity_type,
                'object_id': log.entity_id,
                'ip_address': log.ip_address,
                'timestamp': log.timestamp.isoformat(),
            })
        return Response(data)

# =============================================================================
# Resolution Endpoints (Tickets & Disputes)
# =============================================================================

class AdminSupportTicketDetailView(APIView):
    """View and respond to support tickets."""
    permission_classes = [IsDashboardUser]

    def get(self, request, pk):
        from support_tickets.models import Ticket, TicketMessage
        from django.shortcuts import get_object_or_404
        
        ticket = get_object_or_404(Ticket, pk=pk)
        messages = ticket.messages.select_related('sender').all()
        
        data = {
            'id': ticket.id,
            'user_email': ticket.user.email if ticket.user else '',
            'user_name': f"{ticket.user.first_name} {ticket.user.last_name}" if ticket.user else '',
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'created_at': ticket.created_at.isoformat(),
            'messages': [{
                'id': m.id,
                'sender': m.sender.email if m.sender else 'Unknown',
                'is_admin': m.sender.is_staff if m.sender else False,
                'message': m.message,
                'attachment': m.attachment.url if m.attachment else None,
                'created_at': m.created_at.isoformat(),
            } for m in messages]
        }
        return Response(data)

    def post(self, request, pk):
        from support_tickets.models import Ticket, TicketMessage
        from django.shortcuts import get_object_or_404
        
        ticket = get_object_or_404(Ticket, pk=pk)
        
        message_text = request.data.get('message')
        status_update = request.data.get('status')
        
        if message_text:
            TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message_text
            )
            
        if status_update and status_update in [s[0] for s in Ticket.Status.choices]:
            ticket.status = status_update
            ticket.save()
            
            log_audit_action(
                user=request.user,
                action=f"Updated support ticket #{ticket.id} status to {status_update}",
                ip_address=request.META.get('REMOTE_ADDR'),
                content_object=ticket
            )
            
        return Response({'success': True, 'message': 'Ticket updated'})

class AdminDisputeDetailView(APIView):
    """View and resolve disputes."""
    permission_classes = [IsDashboardUser]

    def get(self, request, pk):
        from disputes.models import Dispute
        from django.shortcuts import get_object_or_404
        
        dispute = get_object_or_404(Dispute, pk=pk)
        
        data = {
            'id': dispute.id,
            'reason': dispute.reason,
            'status': dispute.status,
            'admin_resolution': dispute.admin_resolution,
            'created_at': dispute.created_at.isoformat(),
            'customer': {
                'id': dispute.customer.id if dispute.customer else None,
                'email': dispute.customer.email if dispute.customer else '',
                'name': f"{dispute.customer.first_name} {dispute.customer.last_name}" if dispute.customer else '',
            },
            'supplier': {
                'id': dispute.supplier.id if dispute.supplier else None,
                'email': dispute.supplier.email if dispute.supplier else '',
                'name': f"{dispute.supplier.first_name} {dispute.supplier.last_name}" if dispute.supplier else '',
            },
            'order': {
                'order_number': dispute.order.order_number if dispute.order else None,
                'amount': float(dispute.order.final_amount) if dispute.order else 0,
            } if dispute.order else None,
        }
        return Response(data)

    def patch(self, request, pk):
        from disputes.models import Dispute
        from django.shortcuts import get_object_or_404
        
        dispute = get_object_or_404(Dispute, pk=pk)
        
        resolution = request.data.get('admin_resolution')
        status_update = request.data.get('status')
        
        if resolution is not None:
            dispute.admin_resolution = resolution
            
        if status_update and status_update in [s[0] for s in Dispute.Status.choices]:
            dispute.status = status_update
            
        dispute.save()
        
        log_audit_action(
            user=request.user,
            action=f"Resolved dispute #{dispute.id} with status {status_update}",
            ip_address=request.META.get('REMOTE_ADDR'),
            content_object=dispute
        )
            
        return Response({'success': True, 'message': 'Dispute updated'})
