document.addEventListener('DOMContentLoaded', function() {
    // Détection de l'étape actuelle depuis l'URL ou les données de la page
    const urlParams = new URLSearchParams(window.location.search);
    const currentStep = parseInt(urlParams.get('step')) || 1;
    
    // Détection du mode (création ou édition) depuis le container
    const container = document.querySelector('.container[data-is-edit]');
    const isEdit = container ? container.dataset.isEdit === 'True' : false;
    const businessId = container ? container.dataset.businessId : null;
    const localStorageKey = businessId ? `wizard_business_location_create_${businessId}` : null;

    // Gestion du bouton de réinitialisation
    const resetBtn = document.getElementById('resetWizardBtn');
    if (resetBtn && !isEdit) {
        resetBtn.addEventListener('click', function() {
            if (confirm('Êtes-vous sûr de vouloir recommencer le wizard ? Toutes les données saisies seront perdues.')) {
                // Nettoyer le localStorage
                if (localStorageKey) {
                    localStorage.removeItem(localStorageKey);
                    localStorage.removeItem(`wizard_business_location_hours_${businessId}`);
                    localStorage.removeItem(`wizard_business_location_amenities_${businessId}`);
                }
                
                // Rediriger vers l'URL de réinitialisation côté serveur
                const resetUrl = `/business/location/wizard/reset/${businessId}/`;
                window.location.href = resetUrl;
            }
        });
    }

    // Initialisation du datepicker
    if (window.flatpickr) {
        flatpickr('#founded_date', {
            locale: 'fr',
            dateFormat: 'Y-m-d',
            maxDate: 'today',
            allowInput: true
        });
    }

    // Restauration du brouillon si présent (création uniquement)
    if (!isEdit && localStorageKey && localStorage.getItem(localStorageKey)) {
        try {
            const saved = JSON.parse(localStorage.getItem(localStorageKey));
            Object.entries(saved).forEach(([key, value]) => {
                const input = document.querySelector(`[name="${key}"]`);
                if (input) input.value = value;
            });
        } catch (e) { /* ignore */ }
    }

    // Sauvegarde automatique dans localStorage à chaque modification (création uniquement)
    if (!isEdit && localStorageKey) {
        document.querySelectorAll('input, textarea, select').forEach(input => {
            input.addEventListener('input', function() {
                const data = {};
                document.querySelectorAll('input, textarea, select').forEach(f => {
                    data[f.name] = f.value;
                });
                localStorage.setItem(localStorageKey, JSON.stringify(data));
            });
        });
    }

    // Validation et passage à l'étape suivante pour l'étape 1
    const step1Form = document.getElementById('wizardStep1Form');
    if (step1Form) {
        step1Form.querySelector('.btn-next-step').addEventListener('click', function(e) {
            e.preventDefault();
            let isValid = true;
            // Réinitialiser les erreurs
            step1Form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

            // Champs requis
            const requiredFields = ['name', 'business_location_type', 'description', 'city'];
            requiredFields.forEach(field => {
                const input = step1Form.querySelector(`[name="${field}"]`);
                if (input && !input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                }
            });

            if (!isValid) {
                step1Form.scrollIntoView({behavior: 'smooth'});
                return;
            }

            // Passage à l'étape suivante
            step1Form.submit();
        });
    }
});

// Wizard Step 2: Horaires d'ouverture
(function() {
    const form = document.getElementById('wizardStep2Form');
    if (!form) return;

    // Détection du mode (création ou édition) depuis le container
    const container = document.querySelector('.container[data-is-edit]');
    const isEdit = container ? container.dataset.isEdit === 'True' : false;
    const businessId = container ? container.dataset.businessId : null;
    const localStorageKey = businessId ? `wizard_business_location_hours_${businessId}` : null;
    const DAYS = [0,1,2,3,4,5,6];

    // Restauration du brouillon si présent (création uniquement)
    if (!isEdit && localStorageKey && localStorage.getItem(localStorageKey)) {
        try {
            const saved = JSON.parse(localStorage.getItem(localStorageKey));
            Object.entries(saved).forEach(([key, value]) => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'checkbox') input.checked = !!value;
                    else input.value = value;
                }
            });
            // Réactiver/désactiver les champs selon les checkboxes
            form.querySelectorAll('.is-open-checkbox').forEach(checkbox => {
                const day = checkbox.name.split('_')[2];
                const row = form.querySelector(`tr[data-day="${day}"]`);
                if (row) {
                    row.querySelectorAll('input[type="time"]').forEach(input => {
                        input.disabled = !checkbox.checked;
                    });
                }
            });
        } catch (e) { /* ignore */ }
    }

    // Sauvegarde automatique dans localStorage à chaque modification (création uniquement)
    if (!isEdit && localStorageKey) {
        form.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('input', function() {
                const data = {};
                form.querySelectorAll('input, select').forEach(f => {
                    data[f.name] = f.type === 'checkbox' ? f.checked : f.value;
                });
                localStorage.setItem(localStorageKey, JSON.stringify(data));
            });
        });
    }

    // Activer/désactiver les champs horaires selon la case "ouvert/fermé"
    form.querySelectorAll('.is-open-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const day = this.name.split('_')[2];
            const row = form.querySelector(`tr[data-day="${day}"]`);
            if (row) {
                const timeInputs = row.querySelectorAll('input[type="time"]');
                timeInputs.forEach(input => {
                    input.disabled = !this.checked;
                    if (!this.checked) {
                        input.value = '';
                        input.classList.remove('is-invalid');
                    }
                });
            }
        });
    });

    // Validation en temps réel des horaires
    function validateTimeInputs(row) {
        const isOpen = row.querySelector('.is-open-checkbox').checked;
        if (!isOpen) return true;

        const opening = row.querySelector('.opening-time');
        const closing = row.querySelector('.closing-time');
        const breakStart = row.querySelector('.break-start');
        const breakEnd = row.querySelector('.break-end');

        let isValid = true;

        // Validation des heures principales
        if (!opening.value || !closing.value) {
            opening.classList.add('is-invalid');
            closing.classList.add('is-invalid');
            isValid = false;
        } else if (closing.value <= opening.value) {
            opening.classList.add('is-invalid');
            closing.classList.add('is-invalid');
            isValid = false;
        } else {
            opening.classList.remove('is-invalid');
            closing.classList.remove('is-invalid');
        }

        // Validation des pauses
        if (breakStart.value || breakEnd.value) {
            if (!breakStart.value || !breakEnd.value) {
                breakStart.classList.add('is-invalid');
                breakEnd.classList.add('is-invalid');
                isValid = false;
            } else if (breakEnd.value <= breakStart.value) {
                breakStart.classList.add('is-invalid');
                breakEnd.classList.add('is-invalid');
                isValid = false;
            } else if (opening.value && breakStart.value < opening.value) {
                breakStart.classList.add('is-invalid');
                isValid = false;
            } else if (closing.value && breakEnd.value > closing.value) {
                breakEnd.classList.add('is-invalid');
                isValid = false;
            } else {
                breakStart.classList.remove('is-invalid');
                breakEnd.classList.remove('is-invalid');
            }
        } else {
            breakStart.classList.remove('is-invalid');
            breakEnd.classList.remove('is-invalid');
        }

        return isValid;
    }

    // Validation en temps réel
    form.querySelectorAll('input[type="time"]').forEach(input => {
        input.addEventListener('change', function() {
            const row = this.closest('tr');
            if (row) {
                validateTimeInputs(row);
            }
        });
    });

    // Bouton pour dupliquer les horaires d'un jour sur les autres
    form.querySelectorAll('.btn-duplicate').forEach(btn => {
        btn.addEventListener('click', function() {
            const day = this.dataset.day;
            const row = form.querySelector(`tr[data-day="${day}"]`);
            if (!row) return;
            
            const isOpen = row.querySelector('.is-open-checkbox').checked;
            const opening = row.querySelector('.opening-time').value;
            const closing = row.querySelector('.closing-time').value;
            const breakStart = row.querySelector('.break-start').value;
            const breakEnd = row.querySelector('.break-end').value;
            
            DAYS.forEach(d => {
                if (String(d) === String(day)) return;
                const r = form.querySelector(`tr[data-day="${d}"]`);
                if (r) {
                    r.querySelector('.is-open-checkbox').checked = isOpen;
                    r.querySelectorAll('input[type="time"]').forEach(input => {
                        input.disabled = !isOpen;
                    });
                    r.querySelector('.opening-time').value = opening;
                    r.querySelector('.closing-time').value = closing;
                    r.querySelector('.break-start').value = breakStart;
                    r.querySelector('.break-end').value = breakEnd;
                    
                    // Valider la ligne dupliquée
                    validateTimeInputs(r);
                }
            });
        });
    });

    // Validation des horaires à la soumission
    const nextBtn = form.querySelector('.btn-next-step');
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            let isValid = true;
            
            // Réinitialiser les erreurs
            form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            
            // Supprimer les messages d'erreur existants
            form.querySelectorAll('.alert-danger').forEach(alert => alert.remove());

            // Vérifier qu'au moins un jour est ouvert
            const openDays = form.querySelectorAll('.is-open-checkbox:checked');
            if (openDays.length === 0) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger mb-3';
                errorDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i><strong>Veuillez sélectionner au moins un jour d\'ouverture.</strong>';
                form.insertBefore(errorDiv, form.firstChild);
                form.scrollIntoView({behavior: 'smooth'});
                return;
            }

            // Valider chaque ligne
            DAYS.forEach(day => {
                const row = form.querySelector(`tr[data-day="${day}"]`);
                if (row) {
                    if (!validateTimeInputs(row)) {
                        isValid = false;
                    }
                }
            });

            if (!isValid) {
                // Ajouter un message d'erreur global
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger mb-3';
                errorDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i><strong>Veuillez corriger les erreurs dans les horaires avant de continuer.</strong>';
                form.insertBefore(errorDiv, form.firstChild);
                form.scrollIntoView({behavior: 'smooth'});
                return;
            }
            
            // Passage à l'étape suivante
            form.submit();
        });
    }

    // Navigation Précédent
    const prevBtn = form.querySelector('.btn-prev-step');
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            const url = new URL(window.location.href);
            url.searchParams.set('step', '1');
            window.location.href = url.toString();
        });
    }
})();

// Wizard Step 3: Commodités
(function() {
    const form = document.getElementById('wizardStep3Form');
    if (!form) return;

    // Détection du mode (création ou édition) depuis le container
    const container = document.querySelector('.container[data-is-edit]');
    const isEdit = container ? container.dataset.isEdit === 'True' : false;
    const businessId = container ? container.dataset.businessId : null;
    const localStorageKey = businessId ? `wizard_business_location_amenities_${businessId}` : null;

    // Restauration du brouillon si présent (création uniquement)
    if (!isEdit && localStorageKey && localStorage.getItem(localStorageKey)) {
        try {
            const saved = JSON.parse(localStorage.getItem(localStorageKey));
            Object.entries(saved).forEach(([key, value]) => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    if (input.type === 'checkbox') input.checked = !!value;
                    else input.value = value;
                }
            });
        } catch (e) { /* ignore */ }
    }

    // Sauvegarde automatique dans localStorage à chaque modification (création uniquement)
    if (!isEdit && localStorageKey) {
        form.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('input', function() {
                const data = {};
                form.querySelectorAll('input, select').forEach(f => {
                    data[f.name] = f.type === 'checkbox' ? f.checked : f.value;
                });
                localStorage.setItem(localStorageKey, JSON.stringify(data));
            });
        });
    }

    // Afficher/masquer le champ détail selon la sélection de la commodité
    form.querySelectorAll('.amenity-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const amenityId = this.dataset.amenityId;
            const detailsInput = form.querySelector(`[name="details_${amenityId}"]`);
            if (detailsInput) {
                const detailsContainer = detailsInput.closest('.amenity-details-input') || detailsInput.parentElement;
                if (this.checked) {
                    detailsContainer.style.display = 'block';
                } else {
                    detailsContainer.style.display = 'none';
                    detailsInput.value = '';
                }
            }
        });
    });

    // Validation à la soumission (au moins une commodité sélectionnée)
    const nextBtn = form.querySelector('.btn-next-step');
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            let isValid = true;
            // Réinitialiser les erreurs
            form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

            const checked = form.querySelectorAll('.amenity-checkbox:checked');
            if (checked.length === 0) {
                // Afficher une erreur globale
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-danger';
                errorDiv.textContent = 'Veuillez sélectionner au moins une commodité.';
                form.insertBefore(errorDiv, form.firstChild);
                isValid = false;
            }

            if (!isValid) {
                form.scrollIntoView({behavior: 'smooth'});
                return;
            }
            // Passage à l'étape suivante
            form.submit();
        });
    }

    // Navigation Précédent
    const prevBtn = form.querySelector('.btn-prev-step');
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            const url = new URL(window.location.href);
            url.searchParams.set('step', '2');
            window.location.href = url.toString();
        });
    }
})();

// Wizard Step 4: Résumé
(function() {
    const form = document.getElementById('wizardStep4Form');
    if (!form) return;

    // Détection du mode (création ou édition) depuis le container
    const container = document.querySelector('.container[data-is-edit]');
    const isEdit = container ? container.dataset.isEdit === 'True' : false;
    const businessId = container ? container.dataset.businessId : null;
    const localStorageKeys = businessId ? [
        `wizard_business_location_create_${businessId}`,
        `wizard_business_location_hours_${businessId}`,
        `wizard_business_location_amenities_${businessId}`
    ] : [];

    // Navigation Précédent
    const prevBtn = form.querySelector('.btn-prev-step');
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            const url = new URL(window.location.href);
            url.searchParams.set('step', '3');
            window.location.href = url.toString();
        });
    }

    // Validation finale et soumission
    form.querySelector('.btn-next-step').addEventListener('click', function(e) {
        // Nettoyage du localStorage après validation (création uniquement)
        if (!isEdit && localStorageKeys.length) {
            localStorageKeys.forEach(key => localStorage.removeItem(key));
        }
        form.submit();
    });
})();

// Wizard Step 5: Images (Drag & Drop, AJAX)
(function() {
    const form = document.getElementById('wizardStep5Form');
    if (!form) return;

    const dropZone = document.getElementById('imageDropZone');
    const fileInput = document.getElementById('imageInput');
    const previewList = document.getElementById('imagePreviewList');
    const errorDiv = document.getElementById('imageDropZoneError');
    
    if (!dropZone || !fileInput || !previewList || !errorDiv) return;
    
    let images = [];
    let uploading = false;
    const MAX_IMAGES = 5;

    // Helper pour afficher les miniatures
    function renderPreviews() {
        previewList.innerHTML = '';
        images.forEach((img, idx) => {
            const col = document.createElement('div');
            col.className = 'col-6 col-md-4 col-lg-3';
            col.innerHTML = `
                <div class="card position-relative">
                    <img src="${img.url}" class="card-img-top" style="object-fit:cover;height:120px;">
                    <div class="card-body py-2 px-2">
                        <input type="radio" name="is_primary" class="form-check-input me-1" value="${img.id}" id="primary_${img.id}" ${img.is_primary ? 'checked' : ''}>
                        <label for="primary_${img.id}" class="form-check-label small">Image principale</label>
                        <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1 btn-delete-image" data-id="${img.id}"><i class="fas fa-times"></i></button>
                    </div>
                </div>
            `;
            previewList.appendChild(col);
        });
        
        // Bind suppression
        previewList.querySelectorAll('.btn-delete-image').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                deleteImage(id);
            });
        });
        
        // Bind choix principal
        previewList.querySelectorAll('input[name="is_primary"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const selectedId = parseInt(this.value);
                // Réinitialiser toutes les images
                images.forEach(img => img.is_primary = false);
                // Marquer l'image sélectionnée comme principale
                const selectedImage = images.find(img => img.id === selectedId);
                if (selectedImage) {
                    selectedImage.is_primary = true;
                }
                renderPreviews();
            });
        });
    }

    // Upload AJAX
    function uploadFiles(files) {
        if (uploading) return;
        if (images.length + files.length > MAX_IMAGES) {
            errorDiv.textContent = `Maximum ${MAX_IMAGES} images.`;
            errorDiv.style.display = 'block';
            return;
        }
        errorDiv.style.display = 'none';
        uploading = true;
        
        Array.from(files).forEach(file => {
            const formData = new FormData();
            formData.append('image', file);
            
            fetch('/business/location/upload-image-temp/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
                }
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    const newImage = {
                        id: parseInt(data.id),
                        url: data.url,
                        is_primary: images.length === 0 // La première image est principale par défaut
                    };
                    images.push(newImage);
                    renderPreviews();
                } else {
                    errorDiv.textContent = data.error || 'Erreur lors de l\'upload.';
                    errorDiv.style.display = 'block';
                }
            })
            .catch(() => {
                errorDiv.textContent = 'Erreur lors de l\'upload.';
                errorDiv.style.display = 'block';
            })
            .finally(() => {
                uploading = false;
            });
        });
    }

    // Suppression AJAX
    function deleteImage(id) {
        fetch(`/business/location/delete-image-temp/${id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
            }
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.success) {
                // Supprimer l'image du tableau local
                images = images.filter(img => img.id !== id);
                
                // Si l'image supprimée était principale et qu'il reste des images, en choisir une autre
                if (!images.some(img => img.is_primary) && images.length > 0) {
                    images[0].is_primary = true;
                }
                
                renderPreviews();
            } else {
                errorDiv.textContent = data.error || 'Erreur lors de la suppression.';
                errorDiv.style.display = 'block';
            }
        })
        .catch(() => {
            errorDiv.textContent = 'Erreur lors de la suppression.';
            errorDiv.style.display = 'block';
        });
    }

    // Drag & drop
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('bg-primary', 'text-white');
    });
    dropZone.addEventListener('dragleave', e => {
        e.preventDefault();
        dropZone.classList.remove('bg-primary', 'text-white');
    });
    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('bg-primary', 'text-white');
        uploadFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', function() {
        uploadFiles(this.files);
        this.value = '';
    });

    // Initial fetch (pour édition ou reload)
    function fetchImages() {
        fetch('/business/location/list-image-temp/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
            }
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.images) {
                // Convertir les IDs en nombres et s'assurer qu'une image est principale
                images = data.images.map((img, index) => ({
                    id: parseInt(img.id),
                    url: img.url,
                    is_primary: index === 0 // La première image est principale par défaut
                }));
                renderPreviews();
            }
        })
        .catch(() => {
            errorDiv.textContent = 'Erreur lors du chargement des images.';
            errorDiv.style.display = 'block';
        });
    }
    fetchImages();

    // Navigation Précédent
    const prevBtn = form.querySelector('.btn-prev-step');
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            const url = new URL(window.location.href);
            url.searchParams.set('step', '4');
            window.location.href = url.toString();
        });
    }

    // Validation finale et soumission
    const nextBtn = form.querySelector('.btn-finish-step');
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // On s'assure qu'il y a au moins une image
            if (images.length === 0) {
                errorDiv.textContent = 'Veuillez ajouter au moins une image.';
                errorDiv.style.display = 'block';
                return;
            }
            
            // On s'assure qu'une image principale est choisie
            if (!images.some(img => img.is_primary)) {
                errorDiv.textContent = 'Veuillez choisir une image principale.';
                errorDiv.style.display = 'block';
                return;
            }
            
            // Masquer les erreurs si tout est OK
            errorDiv.style.display = 'none';
            
            // Soumettre le formulaire
            form.submit();
        });
    }
})();

// Leaflet Map Modal Logic (Step 1)
(function() {
    const openBtn = document.getElementById('openMapModal');
    if (!openBtn) return;
    
    let map, marker;
    let selectedLatLng = null;
    let mapModal = new bootstrap.Modal(document.getElementById('mapModal'));
    const confirmBtn = document.getElementById('confirmMapSelection');
    const mapStatus = document.getElementById('mapStatus');
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');
    
    // Champs d'adresse à remplir
    const streetInput = document.getElementById('street_address');
    const cityInput = document.getElementById('city');
    const regionInput = document.getElementById('region');
    const countryInput = document.getElementById('country');
    const postalInput = document.getElementById('postal_code');
    const neighborhoodInput = document.getElementById('neighborhood');

    openBtn.addEventListener('click', function() {
        mapModal.show();
        setTimeout(() => {
            if (!map) {
                // Initialiser la carte avec le Cameroun comme centre par défaut
                map = L.map('leafletMap').setView([4.05, 9.7], 7);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }).addTo(map);
                
                map.on('click', function(e) {
                    if (marker) map.removeLayer(marker);
                    marker = L.marker(e.latlng).addTo(map);
                    selectedLatLng = e.latlng;
                    mapStatus.textContent = 'Lat: ' + e.latlng.lat.toFixed(6) + ', Lon: ' + e.latlng.lng.toFixed(6) + '...';
                    
                    // Appel Nominatim reverse geocoding
                    fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${e.latlng.lat}&lon=${e.latlng.lng}`)
                        .then(resp => resp.json())
                        .then(data => {
                            mapStatus.textContent = data.display_name || '';
                            // Remplir les champs d'adresse si dispo
                            if (data.address) {
                                if (streetInput) streetInput.value = data.address.road || '';
                                if (cityInput) cityInput.value = data.address.city || data.address.town || data.address.village || '';
                                if (regionInput) regionInput.value = data.address.state || '';
                                if (countryInput) countryInput.value = data.address.country || '';
                                if (postalInput) postalInput.value = data.address.postcode || '';
                                if (neighborhoodInput) neighborhoodInput.value = data.address.suburb || '';
                            }
                        })
                        .catch(() => {
                            mapStatus.textContent = 'Reverse geocoding échoué.';
                        });
                });
            } else {
                map.invalidateSize();
            }
        }, 300);
    });

    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (selectedLatLng) {
                if (latInput) latInput.value = selectedLatLng.lat.toFixed(8);
                if (lonInput) lonInput.value = selectedLatLng.lng.toFixed(8);
            }
            mapModal.hide();
        });
    }

    // Reset marker/selection à chaque ouverture
    const mapModalElement = document.getElementById('mapModal');
    if (mapModalElement) {
        mapModalElement.addEventListener('show.bs.modal', function() {
            selectedLatLng = null;
            if (mapStatus) mapStatus.textContent = '';
            if (marker && map) {
                map.removeLayer(marker);
                marker = null;
            }
        });
    }
})(); 