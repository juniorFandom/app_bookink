from .web import (
    # Food Category views
    food_category_list,
    food_category_create,
    food_category_detail,
    food_category_edit,
    food_category_delete,
    
    # Menu Item views
    menu_item_list,
    menu_item_create,
    menu_item_detail,
    menu_item_edit,
    menu_item_delete,
    menu_item_images,
    menu_item_image_add,
    menu_item_image_delete,
    
    # Order views
    order_list,
    order_create,
    order_detail,
    order_edit,
    order_cancel,
    order_status_update,
    order_payment_update,
    order_item_add,
    order_item_edit,
    order_item_delete,
    
    # API views
    api_menu_items,
    api_order_items,
    api_order_total,
)
