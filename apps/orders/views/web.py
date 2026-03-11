from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import FoodCategory, MenuItem, RestaurantOrder, OrderItem, MenuItemImage
from ..forms import (
    FoodCategoryForm, MenuItemForm, RestaurantOrderForm,
    OrderItemForm, OrderStatusForm, OrderPaymentForm, OrderCancellationForm,
    CustomRestaurantOrderForm, OrderCustomerForm
)
from ..services import OrderService, MenuService
from apps.orders.services.order_service import validate_cart_checkout
from apps.business.templatetags.business_tags import is_owner
from apps.wallets.services.wallet_service import WalletService
from apps.users.models.user import User


class FoodCategoryListView(LoginRequiredMixin, ListView):
    """Display list of food categories."""
    model = FoodCategory
    template_name = 'orders/food_category/list.html'
    context_object_name = 'categories'
    ordering = ['order', 'name']


class FoodCategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new food category."""
    model = FoodCategory
    form_class = FoodCategoryForm
    template_name = 'orders/food_category/form.html'
    success_url = reverse_lazy('orders:category_list')
    success_message = _("Food category '%(name)s' was created successfully")


class FoodCategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update an existing food category."""
    model = FoodCategory
    form_class = FoodCategoryForm
    template_name = 'orders/food_category/form.html'
    success_url = reverse_lazy('orders:category_list')
    success_message = _("Food category '%(name)s' was updated successfully")


class MenuItemListView(LoginRequiredMixin, ListView):
    """Display list of menu items."""
    model = MenuItem
    template_name = 'orders/menu_item/list.html'
    context_object_name = 'menu_items'
    ordering = ['food_category__order', 'food_category__name', 'order', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(business_location__business__owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = FoodCategory.objects.all()
        return context


class MenuItemDetailView(LoginRequiredMixin, DetailView):
    """Display menu item details."""
    model = MenuItem
    template_name = 'orders/menu_item/detail.html'
    context_object_name = 'menu_item'


class MenuItemCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new menu item."""
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'orders/menu_item/form.html'
    success_url = reverse_lazy('orders:menu_item_list')
    success_message = _("Menu item '%(name)s' was created successfully")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['business_location'] = self.request.user.business_location
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle additional images
        files = self.request.FILES.getlist('additional_images')
        if files:
            MenuService.update_menu_item(
                self.object,
                data={'replace_images': form.cleaned_data['replace_images']},
                images=files
            )
        return response


class MenuItemUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update an existing menu item."""
    model = MenuItem
    form_class = MenuItemForm
    template_name = 'orders/menu_item/form.html'
    success_url = reverse_lazy('orders:menu_item_list')
    success_message = _("Menu item '%(name)s' was updated successfully")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['business_location'] = self.object.business_location
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle additional images
        files = self.request.FILES.getlist('additional_images')
        if files:
            MenuService.update_menu_item(
                self.object,
                data={'replace_images': form.cleaned_data['replace_images']},
                images=files
            )
        return response


class RestaurantOrderListView(LoginRequiredMixin, ListView):
    """Display list of restaurant orders."""
    model = RestaurantOrder
    template_name = 'orders/order/list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        location_id = self.request.GET.get('location')
        if location_id:
            queryset = queryset.filter(business_location_id=location_id)
        elif self.request.user.is_staff:
            return queryset
        elif hasattr(self.request.user, 'business_location'):
            return queryset.filter(business_location=self.request.user.business_location)
        else:
            return queryset.filter(customer=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filters'] = RestaurantOrder.STATUS_CHOICES
        location_id = self.request.GET.get('location')
        if location_id:
            from apps.business.models import BusinessLocation
            context['filtered_location'] = BusinessLocation.objects.filter(pk=location_id).first()
        return context


class RestaurantOrderDetailView(LoginRequiredMixin, DetailView):
    """Display restaurant order details."""
    model = RestaurantOrder
    template_name = 'orders/order/detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff or (
            hasattr(self.request.user, 'business_location') and
            self.object.business_location == self.request.user.business_location
        ):
            context['status_form'] = OrderStatusForm(instance=self.object)
        return context


class RestaurantOrderCreateView(LoginRequiredMixin, CreateView):
    """Create a new restaurant order."""
    model = RestaurantOrder
    form_class = RestaurantOrderForm
    template_name = 'orders/order/form.html'
    success_url = reverse_lazy('orders:order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_form'] = OrderItemForm(
            business_location=self.request.user.business_location
        )
        return context

    def form_valid(self, form):
        try:
            order = OrderService.create_order(
                business_location=self.request.user.business_location,
                customer=self.request.user,
                items_data=self.request.POST.getlist('items'),
                **form.cleaned_data
            )
            messages.success(
                self.request,
                _("Order %(number)s was created successfully") % {'number': order.order_number}
            )
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


def update_order_status(request, pk):
    """Update the status of a restaurant order."""
    order = get_object_or_404(RestaurantOrder, pk=pk)
    
    # Check permissions
    if not request.user.is_staff and (
        not hasattr(request.user, 'business_location') or
        order.business_location != request.user.business_location
    ):
        messages.error(request, _("You don't have permission to update this order"))
        return redirect('orders:order_detail', pk=pk)

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            try:
                OrderService.update_order_status(
                    order,
                    form.cleaned_data['status'],
                    notes=form.cleaned_data.get('restaurant_notes')
                )
                messages.success(request, _("Order status updated successfully"))
            except Exception as e:
                messages.error(request, str(e))
    
    return redirect('orders:order_detail', pk=pk)


# Food Category Views
@login_required
def food_category_list(request):
    """List all food categories."""
    categories = FoodCategory.objects.all()
    return render(request, 'orders/food_category_list.html', {
        'categories': categories
    })


@login_required
def food_category_create(request):
    """Create a new food category."""
    if request.method == 'POST':
        form = FoodCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('orders:food_category_list')
    else:
        form = FoodCategoryForm()
    
    return render(request, 'orders/food_category/form.html', {'form': form})


@login_required
def food_category_detail(request, pk):
    """View food category details."""
    category = get_object_or_404(FoodCategory, pk=pk)
    menu_items = category.menu_items.all()
    return render(request, 'orders/food_category_detail.html', {
        'category': category,
        'menu_items': menu_items
    })


@login_required
def food_category_edit(request, pk):
    """Edit a food category."""
    category = get_object_or_404(FoodCategory, pk=pk)
    if request.method == 'POST':
        form = FoodCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('Food category updated successfully.'))
            return redirect('orders:food_category_detail', pk=pk)
    else:
        form = FoodCategoryForm(instance=category)
    
    return render(request, 'orders/food_category/form.html', {
        'form': form,
        'category': category,
        'title': _('Edit Food Category')
    })


@login_required
def food_category_delete(request, pk):
    """Delete a food category."""
    category = get_object_or_404(FoodCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, _('Food category deleted successfully.'))
        return redirect('orders:food_category_list')
    
    return render(request, 'orders/food_category_confirm_delete.html', {
        'category': category
    })


# Menu Item Views
@login_required
def menu_item_list(request):
    """List all menu items."""
    menu_items = MenuItem.objects.all()
    categories = FoodCategory.objects.all()
    return render(request, 'orders/menu_item/list.html', {
        'menu_items': menu_items,
        'categories': categories
    })


@login_required
def menu_item_create(request):
    """Create a new menu item."""
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('orders:menu_item_list')
    else:
        form = MenuItemForm()
    return render(request, 'orders/menu_item/form.html', {
        'form': form,
        'title': _('Create Menu Item')
    })


@login_required
def menu_item_detail(request, pk):
    """View menu item details."""
    menu_item = get_object_or_404(MenuItem, pk=pk)
    images = menu_item.images.all()
    return render(request, 'orders/menu_item_detail.html', {
        'menu_item': menu_item,
        'images': images
    })


@login_required
def menu_item_edit(request, pk):
    """Edit a menu item."""
    menu_item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            form.save()
            messages.success(request, _('Menu item updated successfully.'))
            return redirect('orders:menu_item_detail', pk=pk)
    else:
        form = MenuItemForm(instance=menu_item)
    
    return render(request, 'orders/menu_item/form.html', {
        'form': form,
        'title': _('Edit Menu Item')
    })


@login_required
def menu_item_delete(request, pk):
    """Delete a menu item."""
    menu_item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        menu_item.delete()
        messages.success(request, _('Menu item deleted successfully.'))
        return redirect('orders:menu_item_list')
    
    return render(request, 'orders/menu_item_confirm_delete.html', {
        'menu_item': menu_item
    })


@login_required
def menu_item_images(request, pk):
    """Manage menu item images."""
    menu_item = get_object_or_404(MenuItem, pk=pk)
    images = menu_item.images.all()
    return render(request, 'orders/menu_item_images.html', {
        'menu_item': menu_item,
        'images': images
    })


@login_required
def menu_item_image_add(request, pk):
    """Add an image to a menu item."""
    menu_item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.menu_item = menu_item
            image.save()
            messages.success(request, _('Image added successfully.'))
            return redirect('orders:menu_item_images', pk=pk)
    else:
        form = MenuItemImageForm()
    
    return render(request, 'orders/menu_item_image_form.html', {
        'form': form,
        'menu_item': menu_item,
        'title': _('Add Image')
    })


@login_required
def menu_item_image_delete(request, pk, image_id):
    """Delete a menu item image."""
    menu_item = get_object_or_404(MenuItem, pk=pk)
    image = get_object_or_404(MenuItemImage, pk=image_id, menu_item=menu_item)
    if request.method == 'POST':
        image.delete()
        messages.success(request, _('Image deleted successfully.'))
        return redirect('orders:menu_item_images', pk=pk)
    
    return render(request, 'orders/menu_item_image_confirm_delete.html', {
        'menu_item': menu_item,
        'image': image
    })


# Order Views
@login_required
def order_list(request):
    """List all orders."""
    orders = RestaurantOrder.objects.all()
    return render(request, 'orders/order_list.html', {
        'orders': orders
    })


@login_required
def order_create(request):
    business_location = getattr(request.user, 'business_location', None)
    menu_items_in_stock = MenuItem.objects.filter(
        business_location=business_location,
        is_available=True,
        stock_quantity__gt=0
    )
    if request.method == 'POST':
        customer_form = OrderCustomerForm(request.POST)
        form = CustomRestaurantOrderForm(request.POST, business_location=business_location)
        if customer_form.is_valid() and form.is_valid():
            try:
                # Recherche ou création du client
                email = customer_form.cleaned_data['email']
                phone = customer_form.cleaned_data['phone_number']
                user_qs = User.objects.filter(email=email)
                if not user_qs.exists() and phone:
                    user_qs = User.objects.filter(phone_number=phone)
                if user_qs.exists():
                    customer = user_qs.first()
                else:
                    customer = User.objects.create(
                        first_name=customer_form.cleaned_data['first_name'],
                        last_name=customer_form.cleaned_data['last_name'],
                        email=email,
                        phone_number=phone,
                        username=email or phone or f'user_{User.objects.count()+1}'
                    )
                # Créer la commande principale
                order = form.save(commit=False)
                order.customer = customer
                order.business_location = business_location
                order.status = 'READY'
                order.payment_status = 'PAID'
                order.payment_method = 'CASH'
                order.save()
                # Créer les OrderItem à partir des plats sélectionnés
                menu_item_ids = request.POST.getlist('menu_items')
                for item_id in menu_item_ids:
                    try:
                        menu_item = menu_items_in_stock.get(id=item_id)
                        quantity = int(request.POST.get(f'quantity_{item_id}', 1))
                        if quantity > 0 and quantity <= menu_item.stock_quantity:
                            OrderItem.objects.create(
                                restaurant_order=order,
                                menu_item=menu_item,
                                quantity=quantity,
                                unit_price=menu_item.price,
                                total_price=menu_item.price * quantity
                            )
                            menu_item.stock_quantity -= quantity
                            if menu_item.stock_quantity == 0:
                                menu_item.is_available = False
                            menu_item.save()
                    except MenuItem.DoesNotExist:
                        continue
                order.calculate_total()
                order.save()
                messages.success(request, _('Order created successfully.'))
                return redirect('orders:order_detail', order_number=order.order_number)
            except Exception as e:
                messages.error(request, str(e))
        else:
            # Si un des deux formulaires est invalide, on le repasse au template
            pass
    else:
        form = CustomRestaurantOrderForm(business_location=business_location)
        customer_form = OrderCustomerForm()
    return render(request, 'orders/order_form.html', {
        'form': form,
        'customer_form': customer_form,
        'business_location': business_location,
        'menu_items_in_stock': menu_items_in_stock,
        'title': _('Create Order')
    })


@login_required
def order_detail(request, order_number):
    """View order details."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    items = order.items.all()
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': items
    })


@login_required
def order_edit(request, order_number):
    """Edit an order."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    if order.status not in ['PENDING', 'CONFIRMED']:
        messages.error(request, _('Cannot edit order in current status.'))
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        form = RestaurantOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, _('Order updated successfully.'))
            return redirect('orders:order_detail', order_number=order_number)
    else:
        form = RestaurantOrderForm(instance=order)
    
    return render(request, 'orders/order_form.html', {
        'form': form,
        'order': order,
        'title': _('Edit Order')
    })


@login_required
def order_cancel(request, order_number):
    """Cancel an order."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    if order.status in ['DELIVERED', 'CANCELLED', 'REFUNDED']:
        messages.error(request, _('Cannot cancel order in current status.'))
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        form = OrderCancellationForm(request.POST)
        if form.is_valid():
            try:
                OrderService.update_order_status(
                    order,
                    'CANCELLED',
                    cancellation_reason=form.cleaned_data['cancellation_reason']
                )
                messages.success(request, _('Order cancelled successfully.'))
                return redirect('orders:order_detail', order_number=order_number)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = OrderCancellationForm()
    
    return render(request, 'orders/order_cancel.html', {
        'form': form,
        'order': order
    })


@login_required
def order_status_update(request, order_number):
    """Update order status."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            try:
                OrderService.update_order_status(
                    order,
                    form.cleaned_data['status'],
                    notes=form.cleaned_data.get('restaurant_notes')
                )
                messages.success(request, _('Order status updated successfully.'))
                return redirect('orders:order_detail', order_number=order_number)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = OrderStatusForm(instance=order)
    
    return render(request, 'orders/order_status_form.html', {
        'form': form,
        'order': order
    })


@login_required
def order_payment_update(request, order_number):
    """Update order payment status."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    if request.method == 'POST':
        form = OrderPaymentForm(request.POST, instance=order)
        if form.is_valid():
            try:
                OrderService.update_payment_status(
                    order,
                    form.cleaned_data['payment_status']
                )
                messages.success(request, _('Payment status updated successfully.'))
                return redirect('orders:order_detail', order_number=order_number)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = OrderPaymentForm(instance=order)
    
    return render(request, 'orders/order_payment_form.html', {
        'form': form,
        'order': order
    })


@login_required
def order_item_add(request, order_number):
    """Add an item to an order."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    if order.status not in ['PENDING', 'CONFIRMED']:
        messages.error(request, _('Cannot add items to order in current status.'))
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            try:
                OrderService.add_order_item(
                    order,
                    form.cleaned_data['menu_item'],
                    form.cleaned_data['quantity'],
                    special_instructions=form.cleaned_data.get('special_instructions')
                )
                messages.success(request, _('Item added successfully.'))
                return redirect('orders:order_detail', order_number=order_number)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = OrderItemForm()
    
    return render(request, 'orders/order_item_form.html', {
        'form': form,
        'order': order,
        'title': _('Add Item')
    })


@login_required
def order_item_edit(request, order_number, item_id):
    """Edit an order item."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    item = get_object_or_404(OrderItem, pk=item_id, restaurant_order=order)
    if order.status not in ['PENDING', 'CONFIRMED']:
        messages.error(request, _('Cannot edit items in order in current status.'))
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, _('Item updated successfully.'))
            return redirect('orders:order_detail', order_number=order_number)
    else:
        form = OrderItemForm(instance=item)
    
    return render(request, 'orders/order_item_form.html', {
        'form': form,
        'order': order,
        'item': item,
        'title': _('Edit Item')
    })


@login_required
def order_item_delete(request, order_number, item_id):
    """Delete an order item."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    item = get_object_or_404(OrderItem, pk=item_id, restaurant_order=order)
    if order.status not in ['PENDING', 'CONFIRMED']:
        messages.error(request, _('Cannot delete items in order in current status.'))
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, _('Item deleted successfully.'))
        return redirect('orders:order_detail', order_number=order_number)
    
    return render(request, 'orders/order_item_confirm_delete.html', {
        'order': order,
        'item': item
    })


# API Views
@login_required
def api_menu_items(request):
    """API endpoint for menu items."""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    
    menu_items = MenuItem.objects.filter(is_available=True)
    
    if query:
        menu_items = menu_items.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    if category_id:
        menu_items = menu_items.filter(food_category_id=category_id)
    
    data = [{
        'id': item.id,
        'name': item.name,
        'price': float(item.price),
        'description': item.description,
        'image_url': item.main_image.url if item.main_image else None,
    } for item in menu_items]
    
    return JsonResponse({'items': data})


@login_required
def api_order_items(request, order_number):
    """API endpoint for order items."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    items = order.items.all()
    
    data = [{
        'id': item.id,
        'menu_item': {
            'id': item.menu_item.id,
            'name': item.menu_item.name,
            'price': float(item.menu_item.price),
        },
        'quantity': item.quantity,
        'unit_price': float(item.unit_price),
        'total_price': float(item.total_price),
        'special_instructions': item.special_instructions,
    } for item in items]
    
    return JsonResponse({'items': data})


@login_required
def api_order_total(request, order_number):
    """API endpoint for order total."""
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    
    data = {
        'subtotal': float(order.subtotal),
        'tax_amount': float(order.tax_amount),
        'delivery_fee': float(order.delivery_fee),
        'total_amount': float(order.total_amount),
    }
    
    return JsonResponse(data)


@require_POST
@login_required
def add_to_cart(request, pk):
    """Ajoute un plat au panier (session)."""
    menu_item = get_object_or_404(MenuItem, pk=pk, is_available=True, stock_quantity__gt=0)
    cart = request.session.get('cart', {})
    item_id = str(menu_item.pk)
    if item_id in cart:
        cart[item_id]['quantity'] += 1
    else:
        cart[item_id] = {
            'name': menu_item.name,
            'price': float(menu_item.price),
            'quantity': 1,
            'image': menu_item.main_image.url if menu_item.main_image else '',
            'stock_quantity': menu_item.stock_quantity
        }
    # Limiter la quantité au stock disponible
    if cart[item_id]['quantity'] > menu_item.stock_quantity:
        cart[item_id]['quantity'] = menu_item.stock_quantity
        messages.warning(request, _("Stock maximum atteint pour ce plat."))
    else:
        messages.success(request, _(f"{menu_item.name} ajouté au panier."))
    request.session['cart'] = cart
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('orders:menu_item_list')


def restaurant_order_create(request):
    if request.method == 'POST':
        form = RestaurantOrderForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('orders:restaurant_order_list')
    else:
        form = RestaurantOrderForm()
    return render(request, 'orders/order/form.html', {'form': form})


def cart_detail(request):
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render(request, 'orders/cart/detail.html', {'cart': cart, 'total': total})


@require_POST
def cart_clear(request):
    request.session['cart'] = {}
    return redirect('orders:cart_detail')


@require_POST
def cart_update_quantity(request, pk):
    cart = request.session.get('cart', {})
    item_id = str(pk)
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            cart.pop(item_id, None)
        else:
            if item_id in cart:
                cart[item_id]['quantity'] = quantity
        request.session['cart'] = cart
        return JsonResponse({'success': True, 'quantity': quantity})
    except Exception:
        return JsonResponse({'success': False}, status=400)


@require_POST
def cart_remove_item(request, pk):
    cart = request.session.get('cart', {})
    item_id = str(pk)
    if item_id in cart:
        cart.pop(item_id)
        request.session['cart'] = cart
    return redirect('orders:cart_detail')


@require_POST
@login_required
def valider_commande(request):
    cart = request.session.get('cart', {})
    result = validate_cart_checkout(request.user, cart)
    if result['success']:
        request.session['cart'] = {}
        messages.success(request, "Commande validée et payée avec succès !")
        return redirect('orders:order_list')
    else:
        for err in result['errors']:
            messages.error(request, err)
    return redirect('orders:cart_detail')


@login_required
def validate_order(request, order_number):
    order = get_object_or_404(RestaurantOrder, order_number=order_number)
    if order.business_location.business.owner != request.user:
        messages.error(request, _("Vous n'avez pas la permission de valider cette commande."))
        return redirect('orders:order_detail', order_number=order_number)
    if order.status != 'PREPARING':
        messages.error(request, _("La commande n'est pas en cours de préparation."))
        return redirect('orders:order_detail', order_number=order_number)
    if request.method == 'POST':
        try:
            # Passe le statut à DELIVERED
            OrderService.update_order_status(order, 'DELIVERED')
            # Créditer le wallet business
            wallet, created = WalletService.get_or_create_business_wallet(order.business_location.business)
            WalletService.update_wallet_balance(wallet, order.total_amount, 'add')
            messages.success(request, _("Commande validée et wallet crédité."))
        except Exception as e:
            messages.error(request, _(f"Erreur lors de la validation : {e}"))
        return redirect('orders:order_detail', order_number=order_number)
    return redirect('orders:order_detail', order_number=order_number)
