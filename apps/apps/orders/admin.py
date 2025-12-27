from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    RestaurantOrder,
    OrderItem,
    MenuItem,
    MenuItemImage,
    FoodCategory
)


@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    """Admin interface for food categories."""
    list_display = ('name', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'image', 'order', 'is_active')
        }),
    )


class MenuItemImageInline(admin.TabularInline):
    """Inline admin interface for menu item images."""
    model = MenuItemImage
    extra = 1
    fields = ('image', 'caption', 'order')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Admin interface for menu items."""
    list_display = ('name', 'business_location', 'food_category', 'price', 'is_available', 'is_featured')
    list_filter = ('is_available', 'is_featured', 'food_category', 'business_location')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MenuItemImageInline]
    fieldsets = (
        (None, {
            'fields': ('business_location', 'food_category', 'name', 'slug', 'description')
        }),
        (_('Pricing and Availability'), {
            'fields': ('price', 'preparation_time_minutes', 'is_available', 'is_featured', 'order')
        }),
        (_('Nutritional Information'), {
            'fields': ('calories', 'ingredients', 'allergens', 'dietary_info')
        }),
        (_('Images'), {
            'fields': ('main_image',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    """Inline admin interface for order items."""
    model = OrderItem
    extra = 0
    fields = ('menu_item', 'quantity', 'unit_price', 'total_price', 'special_instructions')
    readonly_fields = ('total_price',)


@admin.register(RestaurantOrder)
class RestaurantOrderAdmin(admin.ModelAdmin):
    """Admin interface for restaurant orders."""
    list_display = ('order_number', 'business_location', 'customer', 'order_type', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'order_type', 'business_location')
    search_fields = ('order_number', 'customer__email', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'cancelled_at')
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {
            'fields': ('order_number', 'business_location', 'customer', 'order_type', 'table_number')
        }),
        (_('Delivery Information'), {
            'fields': ('delivery_address', 'delivery_fee', 'estimated_preparation_time')
        }),
        (_('Financial Information'), {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'commission_amount')
        }),
        (_('Status Information'), {
            'fields': ('status', 'payment_status')
        }),
        (_('Notes'), {
            'fields': ('special_instructions', 'customer_notes', 'restaurant_notes')
        }),
        (_('Cancellation Information'), {
            'fields': ('cancellation_reason', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('business_location', 'customer', 'order_type')
        return self.readonly_fields

    def has_add_permission(self, request):
        """Disable manual order creation in admin."""
        return False
