document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Initialize all popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => {
        new bootstrap.Popover(popover);
    });

    // Handle image previews
    const imageInputs = document.querySelectorAll('input[type="file"][accept^="image/"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                const previewContainer = input.closest('.col-md-8');
                let previewImage = previewContainer.querySelector('.image-preview');
                
                if (!previewImage) {
                    previewImage = document.createElement('img');
                    previewImage.classList.add('image-preview');
                    previewContainer.appendChild(previewImage);
                }

                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                };

                reader.readAsDataURL(file);
            }
        });
    });

    // Handle review image gallery
    const reviewImages = document.querySelectorAll('.review-images img');
    reviewImages.forEach(img => {
        img.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('imageModal'));
            const modalImg = document.getElementById('modalImage');
            modalImg.src = this.src;
            modal.show();
        });
    });

    // Handle business hours form
    const businessHoursForm = document.querySelector('.business-hours-form');
    if (businessHoursForm) {
        const closedCheckboxes = businessHoursForm.querySelectorAll('[id$="-is_closed"]');
        closedCheckboxes.forEach(checkbox => {
            const timeInputs = checkbox.closest('.card-body').querySelectorAll('input[type="time"]');
            
            function updateTimeInputs() {
                timeInputs.forEach(input => {
                    input.disabled = checkbox.checked;
                    if (checkbox.checked) {
                        input.value = '';
                    }
                });
            }
            
            checkbox.addEventListener('change', updateTimeInputs);
            updateTimeInputs();
        });
    }

    // Handle amenity form
    const amenityForm = document.querySelector('.amenity-form');
    if (amenityForm) {
        const availableCheckboxes = amenityForm.querySelectorAll('[id$="-is_available"]');
        availableCheckboxes.forEach(checkbox => {
            const details = checkbox.closest('.col-md-6').querySelector('.amenity-details');
            
            function updateDetails() {
                if (details) {
                    details.style.display = checkbox.checked ? 'block' : 'none';
                    const inputs = details.querySelectorAll('input, textarea');
                    inputs.forEach(input => {
                        if (checkbox.checked) {
                            input.disabled = false;
                        } else {
                            input.disabled = true;
                            input.value = '';
                        }
                    });
                }
            }
            
            checkbox.addEventListener('change', updateDetails);
            updateDetails();
        });
    }

    // Handle search form
    const searchForm = document.querySelector('.business-search-form');
    if (searchForm) {
        const clearButton = searchForm.querySelector('.clear-search');
        if (clearButton) {
            clearButton.addEventListener('click', function(event) {
                event.preventDefault();
                const inputs = searchForm.querySelectorAll('input, select');
                inputs.forEach(input => {
                    if (input.type === 'checkbox') {
                        input.checked = false;
                    } else {
                        input.value = '';
                    }
                });
                searchForm.submit();
            });
        }

        // Handle sort dropdown change
        const sortSelect = searchForm.querySelector('#id_sort_by');
        if (sortSelect) {
            sortSelect.addEventListener('change', function() {
                searchForm.submit();
            });
        }
    }

    // Handle review form rating stars
    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach(container => {
        const stars = container.querySelectorAll('label i');
        stars.forEach(star => {
            star.addEventListener('mouseover', function() {
                this.classList.remove('far');
                this.classList.add('fas');
            });
            
            star.addEventListener('mouseout', function() {
                if (!this.closest('label').previousElementSibling.checked) {
                    this.classList.remove('fas');
                    this.classList.add('far');
                }
            });
        });
    });

    // Handle image deletion confirmation
    const deleteImageForms = document.querySelectorAll('.image-delete-form');
    deleteImageForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!confirm('Are you sure you want to delete this image?')) {
                event.preventDefault();
            }
        });
    });

    // Handle map initialization if coordinates are available
    const mapContainer = document.getElementById('businessMap');
    if (mapContainer && mapContainer.dataset.lat && mapContainer.dataset.lng) {
        const map = L.map('businessMap').setView(
            [parseFloat(mapContainer.dataset.lat), parseFloat(mapContainer.dataset.lng)],
            15
        );
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        L.marker([parseFloat(mapContainer.dataset.lat), parseFloat(mapContainer.dataset.lng)])
            .addTo(map)
            .bindPopup(mapContainer.dataset.name);
    }

    // Handle form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Handle loading states
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form && form.checkValidity()) {
                this.classList.add('loading');
                this.disabled = true;
            }
        });
    });
}); 