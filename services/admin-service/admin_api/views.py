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
try:
    from reviews.models import Review
    from accounts.models import User, Customer, Supplier, Delivery
    from course.models import Course, Enrollment
    from notifications.models import Notification
    from orders.models import Order, OrderItem, Coupon
    from payment.models import PaymentHistory
    from products.models import Product, ProImage
    from returnrequest.models import ReturnRequest, Transaction, BalanceWithdrawRequest
except ImportError:
    Review = None
    User = None
    Customer = None
    Supplier = None
    Delivery = None
    Course = None
    Enrollment = None
    Notification = None
    Order = None
    OrderItem = None
    Coupon = None
    PaymentHistory = None
    Product = None
    ProImage = None
    ReturnRequest = None
    Transaction = None
    BalanceWithdrawRequest = None
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
            'role_name': primary_group,
            'profile_picture': user.profile_picture.url if hasattr(user, 'profile_picture') and user.profile_picture else None
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
    """Serve the dashboard single page application."""
    dashboard_dir = os.path.join(settings.BASE_DIR, 'frontend', 'dashboard')
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
            response = HttpResponse(f.read(), content_type=content_type)
            if ext == '.html':
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            return response


def sysadmin_dashboard_view(request, path='index.html'):
    """Serve the system admin dashboard single page application."""
    dashboard_dir = os.path.join(settings.BASE_DIR, 'frontend', 'sysadmin_dashboard')
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
            response = HttpResponse(f.read(), content_type=content_type)
            if ext == '.html':
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            return response



# =============================================================================
# KPI Stats & Chart Endpoints
# =============================================================================

class AdminStatsView(APIView):
    """Aggregated KPI statistics for the dashboard overview."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Revenue from succeeded payments & paid orders
        successful_payments = PaymentHistory.objects.filter(payment_status='succeeded')
        from django.db.models import Q
        paid_orders_all_time = Order.objects.filter(
            Q(paid=True) | Q(id__in=successful_payments.values('order_id'))
        ).distinct()
        
        order_revenue = paid_orders_all_time.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.0')
        course_revenue = successful_payments.filter(course__isnull=False).aggregate(total=Sum('course__Price'))['total'] or Decimal('0.0')
        total_revenue = order_revenue + course_revenue

        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            total_orders = paid_orders_all_time.filter(items__product__Supplier__user=request.user).distinct().count()
        else:
            total_orders = paid_orders_all_time.count() + successful_payments.filter(course__isnull=False).count()
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
        
        # This month paid orders
        this_month_payments = successful_payments.filter(date__gte=month_start)
        this_month_orders_paid = Order.objects.filter(
            Q(paid=True) | Q(id__in=this_month_payments.values('order_id')),
            created_at__gte=month_start
        ).distinct()
        
        # Last month paid orders
        last_month_payments = successful_payments.filter(date__gte=last_month_start, date__lt=month_start)
        last_month_orders_paid = Order.objects.filter(
            Q(paid=True) | Q(id__in=last_month_payments.values('order_id')),
            created_at__gte=last_month_start,
            created_at__lt=month_start
        ).distinct()
        
        if not request.user.is_superuser and getattr(request.user, 'is_supplier', False):
            this_month_orders_paid = this_month_orders_paid.filter(items__product__Supplier__user=request.user).distinct()
            last_month_orders_paid = last_month_orders_paid.filter(items__product__Supplier__user=request.user).distinct()
            this_month_course_revenue = Decimal('0.0')
            last_month_course_revenue = Decimal('0.0')
        else:
            this_month_course_revenue = this_month_payments.filter(course__isnull=False).aggregate(total=Sum('course__Price'))['total'] or Decimal('0.0')
            last_month_course_revenue = last_month_payments.filter(course__isnull=False).aggregate(total=Sum('course__Price'))['total'] or Decimal('0.0')
            
        this_month_revenue = (this_month_orders_paid.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.0')) + this_month_course_revenue
        last_month_revenue = (last_month_orders_paid.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.0')) + last_month_course_revenue
        
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

        # Pad with zeros for the last 6 months to ensure a trend line can be drawn
        from dateutil.relativedelta import relativedelta
        now = timezone.now()
        last_6_months_dates = [now - relativedelta(months=i) for i in range(5, -1, -1)]
        last_6_months_labels = [d.strftime('%b') for d in last_6_months_dates]
        
        results_map = {m['month'].strftime('%b'): float(m['total'] or 0) for m in monthly if m['month']}
        
        revenue_labels = last_6_months_labels
        revenue_data = [results_map.get(label, 0.0) for label in last_6_months_labels]

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
def get_date_range_for_period(period_string):
    from django.utils import timezone
    import datetime
    now = timezone.now()
    if period_string == 'today':
        current_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        prev_start = current_start - datetime.timedelta(days=1)
        prev_end = current_start - datetime.timedelta(microseconds=1)
    elif period_string == 'this_year':
        current_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        prev_start = current_start.replace(year=current_start.year - 1)
        prev_end = current_start - datetime.timedelta(microseconds=1)
    else: # 'this_month'
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        if current_start.month == 1:
            prev_start = current_start.replace(year=current_start.year-1, month=12)
        else:
            prev_start = current_start.replace(month=current_start.month-1)
        prev_end = current_start - datetime.timedelta(microseconds=1)
    return current_start, current_end, prev_start, prev_end



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
                current_start, current_end, prev_start, prev_end = get_date_range_for_period('this_month')
        else:
            try:
                current_start, current_end, prev_start, prev_end = get_date_range_for_period(period)
            except Exception:
                return Response({"error": _("Invalid period")}, status=status.HTTP_400_BAD_REQUEST)
        from Handcrafts.business_config import (
            PLATFORM_PRODUCT_COMMISSION,
            PLATFORM_DELIVERY_MARGIN,
            PLATFORM_COURSE_COMMISSION,
            DEFAULT_CASHBACK_RATE
        )
        from django.db.models import Sum, F

        def calculate_kpis(start_dt, end_dt):
            successful_payments = PaymentHistory.objects.filter(
                payment_status='succeeded',
                date__gte=start_dt,
                date__lte=end_dt
            )
            
            from django.db.models import Q
            # Orders: either marked as paid OR have a succeeded PaymentHistory
            paid_orders = Order.objects.filter(
                Q(paid=True) | Q(id__in=successful_payments.values('order_id')),
                created_at__gte=start_dt,
                created_at__lte=end_dt
            ).distinct()
            
            # Product gross & delivery gross
            total_product_gross = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.0')
            total_delivery_gross = paid_orders.aggregate(total=Sum('delivery_fee'))['total'] or Decimal('0.0')
            total_order_final = paid_orders.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.0')
            
            # Company Earnings from orders
            company_product_earning = total_product_gross * PLATFORM_PRODUCT_COMMISSION
            company_delivery_earning = total_delivery_gross * PLATFORM_DELIVERY_MARGIN
            company_loss_from_cashback = total_order_final * DEFAULT_CASHBACK_RATE
            
            # Refunds
            refunds = ReturnRequest.objects.filter(
                created_at__gte=start_dt,
                created_at__lte=end_dt,
                status=ReturnRequest.ReturnStatus.ACCEPTED
            )
            total_refunded_products = refunds.aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
            company_loss_from_refunds = total_refunded_products * PLATFORM_PRODUCT_COMMISSION
            
            # Course Earnings
            total_course_gross = successful_payments.filter(course__isnull=False).aggregate(total=Sum('course__Price'))['total'] or Decimal('0.0')
            company_course_earning = total_course_gross * PLATFORM_COURSE_COMMISSION
            
            # Gross Income = Total Product Value + Total Delivery Fees + Total Course Value
            total_income = total_product_gross + total_delivery_gross + total_course_gross
            
            # Net Earning = Our exact percentages minus our liabilities
            total_earning = (company_product_earning + company_delivery_earning + company_course_earning) - (company_loss_from_cashback + company_loss_from_refunds)
            
            # Total Outcome = What is NOT ours (Suppliers, Drivers, Instructors) + Full Refunds + Cashbacks
            total_outcome = total_income - total_earning
            
            return float(total_income), float(total_outcome), float(total_earning)

        current_total_income, current_total_outcome, current_earning = calculate_kpis(current_start, current_end)
        prev_total_income, prev_total_outcome, previous_earning = calculate_kpis(prev_start, prev_end)

        # Graph Data Generation
        # Group by month and calculate dynamically
        graph_data = []
        transactions_months = Transaction.objects.filter(
            created_at__gte=current_start,
            created_at__lte=current_end
        ).annotate(month=TruncMonth('created_at')).values('month').distinct().order_by('month')
        
        for tm in transactions_months:
            if not tm['month']: continue
            m_start = tm['month']
            import calendar
            m_end = m_start.replace(day=calendar.monthrange(m_start.year, m_start.month)[1], hour=23, minute=59, second=59)
            m_inc, m_out, m_earn = calculate_kpis(m_start, m_end)
            graph_data.append({
                "month": m_start.strftime("%b"),
                "income": m_inc,
                "outcome": m_out
            })

        percentage_change = 0.0
        if previous_earning > 0:
            percentage_change = float(((current_earning - previous_earning) / previous_earning) * 100)
        elif current_earning > 0:
            percentage_change = 100.0

        # Payment Method Breakdown
        successful_payments_current = PaymentHistory.objects.filter(
            payment_status='succeeded',
            date__gte=current_start,
            date__lte=current_end
        )
        from django.db.models import Q
        payment_methods = Order.objects.filter(
            Q(paid=True) | Q(id__in=successful_payments_current.values('order_id')),
            created_at__gte=current_start,
            created_at__lte=current_end
        ).distinct().values('payment_method').annotate(total=Sum('final_amount')).order_by('-total')
        
        pm_labels = [p['payment_method'] for p in payment_methods]
        pm_data = [float(p['total'] or 0) for p in payment_methods]

        # Quick Stats
        total_customers = User.objects.filter(is_customer=True).count()
        total_products = Product.objects.count()
        avg_rating = Product.objects.aggregate(avg=Avg('Rating'))['avg'] or 0

        return Response({
            'total_income': current_total_income,
            'total_outcome': current_total_outcome,
            'total_earning': current_earning,
            'percentage_change': round(percentage_change, 2),
            'graph_data': graph_data,
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
    """List all orders (proxied from order-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        
        # Proxy request to order-service's admin endpoint
        response = ServiceClient.proxy_request('order-service', '/admin-api/orders/', request)
        if response.status_code != 200:
            return response
            
        data = response.data
        
        # Extract unique user_ids and product_ids to fetch real details
        user_ids = {item['user_id'] for item in data if 'user_id' in item}
        product_ids = set()
        for item in data:
            if 'items' in item:
                for i in item['items']:
                    if 'product_name' in i and str(i['product_name']).startswith("Product "):
                        try:
                            product_ids.add(int(i['product_name'].replace("Product ", "")))
                        except ValueError:
                            pass
        
        try:
            # Stitch User Emails
            if user_ids:
                from accounts.models import User
                users = User.objects.filter(id__in=user_ids).values('id', 'email')
                user_map = {u['id']: u['email'] for u in users}
                for item in data:
                    if item.get('user_id') in user_map:
                        item['user_email'] = user_map[item['user_id']]
                        
            # Stitch Product Names
            if product_ids:
                from products.models import Product
                products = Product.objects.filter(id__in=product_ids).values('id', 'ProductName')
                prod_map = {p['id']: p['ProductName'] for p in products}
                for item in data:
                    if 'items' in item:
                        for i in item['items']:
                            if 'product_name' in i and str(i['product_name']).startswith("Product "):
                                try:
                                    pid = int(i['product_name'].replace("Product ", ""))
                                    if pid in prod_map:
                                        i['product_name'] = prod_map[pid]
                                except ValueError:
                                    pass
        except ImportError:
            pass
                
        return Response(data)


class AdminProductsView(APIView):
    """List all products for admin dashboard (proxied from catalog-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('catalog-service', '/admin-api/products/', request)
        return Response(response.data, status=response.status_code)


class AdminReturnsView(APIView):
    """List all return requests (proxied from order-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('order-service', '/admin-api/returns/', request)
        return Response(response.data, status=response.status_code)


class AdminCoursesView(APIView):
    """List all courses (proxied from catalog-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('catalog-service', '/admin-api/courses/', request)
        return Response(response.data, status=response.status_code)


class AdminReviewsView(APIView):
    """List all reviews (proxied from platform-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('platform-service', '/admin-api/reviews/', request)
        return Response(response.data, status=response.status_code)


class AdminCouponsView(APIView):
    """List all coupons (proxied from order-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('order-service', '/admin-api/coupons/', request)
        return Response(response.data, status=response.status_code)


class AdminTransactionsView(APIView):
    """List all transactions for admin dashboard."""
    permission_classes = [IsDashboardUser]
    """List all transactions (proxied from payment-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('payment-service', '/admin-api/transactions/', request)
        return Response(response.data, status=response.status_code)


class AdminWithdrawalsListView(APIView):
    """List all withdrawal requests (proxied from payment-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('payment-service', '/admin-api/withdrawals/', request)
        return Response(response.data, status=response.status_code)


class AdminNotificationsView(APIView):
    """List all notifications for the current dashboard user/department (proxied from realtime-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('realtime-service', '/admin-api/notifications/', request)
        return Response(response.data, status=response.status_code)

    def post(self, request):
        """Mark all notifications as read (proxied)."""
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('realtime-service', '/admin-api/notifications/', request)
        return Response(response.data, status=response.status_code)


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


class AdminWithdrawalActionView(APIView):
    """Approve or reject a withdrawal (proxied from payment-service)."""
    permission_classes = [IsDashboardUser]

    def post(self, request, pk):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('payment-service', f'/admin-api/withdrawals/{pk}/action/', request)
        return Response(response.data, status=response.status_code)

class AdminReturnActionView(APIView):
    """Approve or reject a return (proxied from order-service)."""
    permission_classes = [IsDashboardUser]

    def post(self, request, pk):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('order-service', f'/admin-api/returns/{pk}/action/', request)
        return Response(response.data, status=response.status_code)

class AdminReviewModerationView(APIView):
    """Approve or reject a review (proxied from platform-service)."""
    permission_classes = [IsDashboardUser]

    def patch(self, request, pk):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('platform-service', f'/admin-api/reviews/{pk}/action/', request)
        return Response(response.data, status=response.status_code)


class AdminPaymentsView(APIView):
    """List all payment history records (proxied from payment-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('payment-service', '/admin-api/payments/', request)
        return Response(response.data, status=response.status_code)


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
    """Return system health (DB, Cache, RabbitMQ, Celery)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        health = {
            "database": "down",
            "redis": "down",
            "rabbitmq": "down",
            "celery": "down"
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
            
        # Check RabbitMQ
        try:
            from celery import Celery
            app = Celery('Handcrafts')
            app.config_from_object('django.conf:settings', namespace='CELERY')
            with app.connection_for_write() as conn:
                conn.connect()
                health["rabbitmq"] = "up"
        except Exception:
            pass
            
        # Check Celery Workers
        try:
            from celery import current_app
            i = current_app.control.inspect()
            stats = i.stats()
            if stats:
                health["celery"] = "up"
        except Exception:
            pass

        # Check Prometheus
        prometheus_url = getattr(settings, 'PROMETHEUS_URL', 'http://prometheus:9090')
        health["prometheus"] = "down"
        health["prometheus_url"] = getattr(settings, 'PROMETHEUS_PUBLIC_URL', 'http://localhost:9090')
        try:
            import urllib.request
            req = urllib.request.urlopen(f"{prometheus_url}/-/healthy", timeout=3)
            if req.status == 200:
                health["prometheus"] = "up"
        except Exception:
            pass

        # Check Grafana
        grafana_url = getattr(settings, 'GRAFANA_URL', 'http://grafana:3000')
        health["grafana"] = "down"
        health["grafana_url"] = getattr(settings, 'GRAFANA_PUBLIC_URL', 'http://localhost:3000')
        try:
            import urllib.request
            req = urllib.request.urlopen(f"{grafana_url}/api/health", timeout=3)
            if req.status == 200:
                health["grafana"] = "up"
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
            'product__Category__Title',
            'product__UnitPrice'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-total_sold')[:5]

        data = []
        for item in top_items:
            name = item['product__ProductName']
            cat = item['product__Category__Title']
            
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
    """List all support tickets (proxied from platform-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('platform-service', '/admin-api/support-tickets/', request)
        return Response(response.data, status=response.status_code)

class AdminDisputesView(APIView):
    """List all disputes (proxied from platform-service)."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('platform-service', '/admin-api/disputes/', request)
        return Response(response.data, status=response.status_code)

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
                except Exception:
                    pass
        return Response({"results": results})

class AdminSendNotificationView(APIView):
    """Send a custom notification to a specific user or all users (proxied from realtime-service)."""
    permission_classes = [IsDashboardUser]

    def post(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('realtime-service', '/admin-api/notifications/send/', request)
        return Response(response.data, status=response.status_code)

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
    """View and manage fraud alerts (proxied from platform-service)."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_view_audit_logs')]

    def get(self, request):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('platform-service', '/admin-api/fraud-alerts/', request)
        return Response(response.data, status=response.status_code)

class AdminFraudAlertActionView(APIView):
    """Resolve or take action on a fraud alert (proxied from platform-service)."""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_suspend_users')]
    
    def post(self, request, pk):
        from internal.service_client import ServiceClient
        response = ServiceClient.proxy_request('platform-service', f'/admin-api/fraud-alerts/{pk}/action/', request)
        return Response(response.data, status=response.status_code)

class AdminProductModerationView(APIView):
    """List products pending moderation."""
    permission_classes = [IsDashboardUser]

    def get(self, request):
        from products.models import Product
        products = Product.objects.select_related('Supplier__user').prefetch_related('images').filter(publish_status=Product.PublishStatus.PENDING)
        data = [{
            'id': p.id,
            'ProductName': p.ProductName,
            'ProductDescription': p.ProductDescription,
            'Supplier': p.Supplier.user.email if p.Supplier and p.Supplier.user else 'Unknown',
            'UnitPrice': float(p.UnitPrice),
            'Stock': p.Stock,
            'Category': p.Category.Title if p.Category else 'N/A',
            'Publish_Date': p.Publish_Date.isoformat() if p.Publish_Date else None,
            'images': [img.image.url for img in p.images.all() if img.image]
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
        reason = request.data.get('reason', '')
        
        if action == 'approve':
            product.publish_status = Product.PublishStatus.APPROVED
            product.save(update_fields=['publish_status'])
            return Response({'status': 'approved'})
        elif action == 'reject':
            product.publish_status = Product.PublishStatus.REJECTED
            if reason:
                product.rejection_reason = reason
                product.save(update_fields=['publish_status', 'rejection_reason'])
            else:
                product.save(update_fields=['publish_status'])
            return Response({'status': 'rejected'})
            
        return Response({'error': 'Invalid action'}, status=400)

class AdminAuditLogsView(APIView):
    """View system audit logs (Admin operations, user changes, etc.)"""
    permission_classes = [IsDashboardUser, require_permission('accounts.can_view_audit_logs')]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        
        # Aggregations
        total_logs = AuditLog.objects.count()
        today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        logs_today = AuditLog.objects.filter(timestamp__gte=today_start).count()
        unique_actors = AuditLog.objects.values('user').distinct().count()
        
        sevendays = timezone.localtime() - timedelta(days=7)
        activity_qs = AuditLog.objects.filter(timestamp__gte=sevendays).annotate(date=TruncDate('timestamp')).values('date').annotate(count=Count('id')).order_by('date')
        
        activity_dict = {item['date']: item['count'] for item in activity_qs if item['date']}
        activity_7_days = []
        for i in range(6, -1, -1):
            dt = (timezone.localtime() - timedelta(days=i)).date()
            activity_7_days.append({
                'date': dt.isoformat(),
                'count': activity_dict.get(dt, 0)
            })
        
        action_qs = AuditLog.objects.values('action').annotate(count=Count('id')).order_by('-count')
        action_distribution = [{'action': item['action'], 'count': item['count']} for item in action_qs]

        # Recent logs
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
            
        return Response({
            'kpis': {
                'total_logs': total_logs,
                'logs_today': logs_today,
                'unique_actors': unique_actors,
            },
            'charts': {
                'activity_7_days': activity_7_days,
                'action_distribution': action_distribution,
            },
            'logs': data
        })


