from celery import shared_task
from .services import ReturnRequestService
from .models import ReturnRequest
from django.core.exceptions import ValidationError
from decimal import Decimal

@shared_task
def create_return_request_task(user_id, product_id, order_id, quantity, reason, image_path=None):
    """
    Asynchronous task to create a return request, its shipments, and send notifications.
    """
    try:
        ReturnRequestService.create_return_request_logic(
            user_id, product_id, order_id, quantity, reason, image_path
        )
    except ValidationError as e:
        # Handle validation errors, perhaps log them
        print(f"Validation error in create_return_request_task: {e}")
    except Exception as e:
        # Handle other unexpected errors
        print(f"An unexpected error occurred in create_return_request_task: {e}")


@shared_task
def process_supplier_approval_task(return_request_id):
    """
    Asynchronous task to process the approval of a return request.
    """
    try:
        return_request = ReturnRequest.objects.get(id=return_request_id)
        ReturnRequestService.process_supplier_approval(return_request)
    except ReturnRequest.DoesNotExist:
        print(f"ReturnRequest with id {return_request_id} not found.")
    except ValidationError as e:
        print(f"Validation error in process_supplier_approval_task: {e}")


@shared_task
def reject_return_request_task(return_request_id):
    """
    Asynchronous task to reject a return request.
    """
    try:
        return_request = ReturnRequest.objects.get(id=return_request_id)
        ReturnRequestService.reject_return_request(return_request)
    except ReturnRequest.DoesNotExist:
        print(f"ReturnRequest with id {return_request_id} not found.")
    except ValidationError as e:
        print(f"Validation error in reject_return_request_task: {e}")


@shared_task
def cancel_return_request_task(return_request_id):
    """
    Asynchronous task to cancel a return request.
    """
    try:
        return_request = ReturnRequest.objects.get(id=return_request_id)
        ReturnRequestService.cancel_return_request(return_request)
    except ReturnRequest.DoesNotExist:
        print(f"ReturnRequest with id {return_request_id} not found.")
    except ValidationError as e:
        print(f"Validation error in cancel_return_request_task: {e}")

