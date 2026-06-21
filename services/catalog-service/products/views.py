"""
catalog/products/views.py — Catalog Service
Cleaned: all commented-out monolithic imports have been removed.
"""
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from craft_common.auth.permissions import HasRole
from craft_common.events.publisher import EventPublisher
from craft_common.events.schemas import (
    ProductCreatedEvent,
    ProductUpdatedEvent,
    ProductStockChangedEvent,
)

from .models import (
    Category,
    MatCategory,
    Product,
    ProImage,
    ProColors,
    ProSizes,
    Posters,
    Collection,
    CollectionItem,
)
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductImageSerializer,
    CollectionSerializer,
)
from .filters import ProductFilter


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("Category", "MatCategory").prefetch_related(
        "images", "Colors", "Sizes"
    )
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class  = ProductFilter
    search_fields    = ["ProductName", "ProductDescription", "Category__Title"]
    ordering_fields  = ["UnitPrice", "Publish_Date", "ProductName"]
    ordering         = ["-Publish_Date"]

    def get_serializer_class(self):
        return ProductSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated(), HasRole("supplier")]

    def perform_create(self, serializer):
        """
        supplier_id is taken directly from the JWT (X-User-ID header).
        No lookup against accounts.Supplier is needed.
        """
        product = serializer.save(supplier_id=self.request.user.id)
        
        # Publish event
        EventPublisher().publish(
            ProductCreatedEvent(
                product_id=product.id,
                supplier_id=product.supplier_id,
                name=product.name,
                price=str(product.price),
            )
        )

        # Trigger Approval Request synchronously (Option A)
        import requests
        try:
            requests.post(
                "http://admin-service:8000/api/workflows/approvals/",
                json={
                    "request_type": "product_approval",
                    "related_object_type": "product",
                    "related_object_id": str(product.id),
                    "assigned_department": "Catalog",
                    "status": "pending"
                },
                headers={"Authorization": self.request.headers.get("Authorization", "")},
                timeout=3
            )
        except requests.RequestException as e:
            import logging
            logging.error(f"Failed to trigger product approval: {e}")

    def perform_update(self, serializer):
        product = serializer.save()
        EventPublisher().publish(
            ProductUpdatedEvent(
                product_id=product.id,
                data=serializer.validated_data,
            )
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, HasRole("supplier")])
    def update_stock(self, request, pk=None):
        """Adjust stock for a product and publish stock_changed event."""
        product   = self.get_object()
        new_stock = request.data.get("stock")
        if new_stock is None:
            return Response(
                {"detail": "stock field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        old_stock     = product.stock
        product.stock = int(new_stock)
        product.save(update_fields=["stock"])

        EventPublisher().publish(
            ProductStockChangedEvent(
                product_id=product.id,
                old_stock=old_stock,
                new_stock=product.stock,
            )
        )
        return Response({"stock": product.stock})

    @action(detail=False, methods=["post"], url_path="bulk-lookup",
            permission_classes=[IsAuthenticated])
    def bulk_lookup(self, request):
        """
        Internal endpoint: returns product snapshots for a list of IDs.
        Used by order-service during cart checkout to validate stock + price.
        POST {"ids": [1, 2, 3]}
        """
        ids      = request.data.get("ids", [])
        products = Product.objects.filter(id__in=ids).values(
            "id", "name", "price", "stock", "supplier_id"
        )
        return Response(list(products))


class CollectionViewSet(viewsets.ModelViewSet):
    queryset         = Collection.objects.prefetch_related("items")
    serializer_class = CollectionSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated(), HasRole("supplier")]
