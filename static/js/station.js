document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('stationSearch');
    const stationsGrid = document.getElementById('stationsGrid');
    const noStationsFound = document.getElementById('noStationsFound');
    const stationCards = document.querySelectorAll('.station-card');

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        let visibleStations = 0;

        if (isListView) {
            // Search in list view
            const listItems = document.querySelectorAll('.list-station-item');
            const alphabetSections = document.querySelectorAll('.alphabet-section');
            
            listItems.forEach(item => {
                const stationName = item.dataset.name.toLowerCase();
                const stationInfo = item.querySelector('.list-station-description')?.textContent.toLowerCase() || '';
                
                if (stationName.includes(searchTerm) || stationInfo.includes(searchTerm)) {
                    item.style.display = 'flex';
                    visibleStations++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Hide/show alphabet sections based on whether they have visible items
            alphabetSections.forEach(section => {
                const visibleItems = section.querySelectorAll('.list-station-item[style*="flex"]');
                if (visibleItems.length > 0 || searchTerm.length === 0) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
            
            if (visibleStations === 0 && searchTerm.length > 0) {
                noStationsFound.style.display = 'block';
                document.getElementById('stationsListView').style.display = 'none';
            } else {
                noStationsFound.style.display = 'none';
                document.getElementById('stationsListView').style.display = 'block';
            }
        } else {
            // Search in grid view (original functionality)
            stationCards.forEach(card => {
                const stationName = card.dataset.name.toLowerCase();
                const stationInfo = card.querySelector('.station-info').textContent.toLowerCase();
                const lines = Array.from(card.querySelectorAll('.line-badge')).map(badge => badge.textContent.toLowerCase()).join(' ');

                if (stationName.includes(searchTerm) || stationInfo.includes(searchTerm) || lines.includes(searchTerm)) {
                    card.style.display = 'block';
                    visibleStations++;
                } else {
                    card.style.display = 'none';
                }
            });

            if (visibleStations === 0 && searchTerm.length > 0) {
                noStationsFound.style.display = 'block';
                stationsGrid.style.display = 'none';
            } else {
                noStationsFound.style.display = 'none';
                stationsGrid.style.display = 'grid';
            }
        }
    });

    stationCards.forEach(card => {
        card.addEventListener('click', function() {
            const stationName = this.dataset.name;
            openStationModal(this, stationName);
        });
    });

    // Station Modal Functions
    async function openStationModal(cardElement, stationName) {
        const modal = document.getElementById('stationModal');
        const modalCard = document.getElementById('stationModalCard');
        
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        // Calculate final modal position (centered)
        const finalWidth = Math.min(600, windowWidth * 0.9);
        const finalHeight = Math.min(windowHeight * 0.8, 800);
        const finalLeft = (windowWidth - finalWidth) / 2;
        const finalTop = (windowHeight - finalHeight) / 2;
        
        // Set initial state - small and centered (GNOME style)
        modalCard.style.left = finalLeft + 'px';
        modalCard.style.top = finalTop + 'px';
        modalCard.style.width = finalWidth + 'px';
        modalCard.style.height = finalHeight + 'px';
        modalCard.style.transform = 'scale(0.6)';
        modalCard.style.opacity = '0';
        modalCard.style.transition = 'all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        
        // Show modal
        modal.classList.add('show');
        
        // Store station name for edit functionality
        modalCard.dataset.stationName = stationName;
        
        // Get station data from the card (for basic info)
        const stationIcon = cardElement.querySelector('.material-symbols').textContent;
        const stationAltName = cardElement.querySelector('.station-alt-name')?.textContent;
        const stationInfo = cardElement.querySelector('.station-info').textContent;
        const stationStatus = cardElement.querySelector('.station-status');
        
        // Get and set station image
        const stationImageHeader = document.getElementById('modalStationImageHeader');
        const cardStyle = cardElement.getAttribute('style');
        const imageMatch = cardStyle?.match(/background-image:\s*url\(['"]?([^'"]*?)['"]?\)/);
        
        if (imageMatch && imageMatch[1] && imageMatch[1] !== '') {
            stationImageHeader.style.backgroundImage = `url('${imageMatch[1]}')`;
            stationImageHeader.style.display = 'block';
        } else {
            stationImageHeader.style.display = 'none';
        }
        
        // Populate basic modal content
        document.getElementById('modalStationIcon').textContent = stationIcon;
        document.getElementById('modalStationName').textContent = stationName;
        document.getElementById('modalStationDescription').textContent = stationInfo;
        
        const altNameElement = document.getElementById('modalStationAltName');
        if (stationAltName) {
            altNameElement.textContent = stationAltName;
            altNameElement.style.display = 'block';
        } else {
            altNameElement.style.display = 'none';
        }
        
        // Copy status
        const modalStatus = document.getElementById('modalStationStatus');
        modalStatus.innerHTML = stationStatus.innerHTML;
        
        // Show loading state for API data
        document.getElementById('modalPlatformCount').textContent = '...';
        document.getElementById('modalStationType').textContent = '...';
        document.getElementById('modalLinesGrid').innerHTML = '<div style="text-align: center; padding: 20px; opacity: 0.7;">Loading lines...</div>';
        
        // Fetch detailed station data from API
        try {
            const response = await fetch(`/api/stations/${encodeURIComponent(stationName)}`);
            if (response.ok) {
                const stationData = await response.json();
                
                // Update modal with real data
                const station = stationData.station;
                const lines = stationData.lines || [];
                const stats = stationData.statistics || {};
                
                document.getElementById('modalPlatformCount').textContent = station.platform_count || stats.platform_count || 'Unknown';
                
                let station_type = "Unknown";
                if (station.type) {
                    switch (station.type) {
                        case 'public':
                            station_type = '🌍 Public Station';
                            break;
                        case 'metro':
                            station_type = '🚇 Metro Station';
                            break;
                        case 'tram':
                            station_type = '🚋 Tram Station';
                            break;
                        case 'bus':
                            station_type = '🚌 Bus Station';
                            break;
                        default:
                            station_type = station.type.charAt(0).toUpperCase() + station.type.slice(1) + ' Station';
                    }
                }

                document.getElementById('modalStationType').textContent = station_type;

                // Populate real lines data
                populateStationLines(lines);
            } else {
                // Fallback to sample data if API fails
                document.getElementById('modalPlatformCount').textContent = 'Unknown';
                document.getElementById('modalStationType').textContent = 'Unknown';
                populateSampleLines();
            }
        } catch (error) {
            console.error('Failed to load station details:', error);
            // Fallback to sample data
            document.getElementById('modalPlatformCount').textContent = 'Unknown';
            document.getElementById('modalStationType').textContent = 'Unknown';
            populateSampleLines();
        }
        
        // Animate to full size with GNOME-style bounce
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                modalCard.style.transform = 'scale(1.02)';
                modalCard.style.opacity = '1';
                
                // Second bounce phase
                setTimeout(() => {
                    modalCard.style.transition = 'transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                    modalCard.style.transform = 'scale(1)';
                }, 400);
            });
        });
    }
    
    function populateStationLines(lines) {
        const linesGrid = document.getElementById('modalLinesGrid');
        
        if (!lines || lines.length === 0) {
            linesGrid.innerHTML = '<div style="text-align: center; padding: 20px; opacity: 0.7;">No lines serve this station</div>';
            return;
        }
        
        linesGrid.innerHTML = lines.map(line => `
            <div class="modal-line-item" style="border-left-color: ${line.color || '#666'}">
                <div class="modal-line-name" style="color: ${line.color || '#666'}">${line.name}
                    ${line.status === "No scheduled service"
                        ? '<div class="modal-line-status">No service</div>'
                        : `<div class="modal-line-status">${line.status || 'Running'}</div>`
                    }
                </div>
                <div class="modal-line-operator">${line.operator_name || line.operator || 'Unknown Operator'}</div>
            </div>
        `).join('');
    }
    
    function populateSampleLines() {
        const sampleLines = [
            { name: 'Loading...', operator: 'Please wait', status: 'Fetching data', color: '#666' }
        ];
        populateStationLines(sampleLines);
    }
    
    function closeStationModal() {
        const modal = document.getElementById('stationModal');
        const modalCard = document.getElementById('stationModalCard');
        
        // Reset to view mode
        document.getElementById('stationEditContent').style.display = 'none';
        document.getElementById('stationViewContent').style.display = 'block';
        
        // Reset form
        document.getElementById('stationEditForm').reset();
        document.getElementById('currentImagePreview').style.display = 'none';
        
        // GNOME-style close animation - shrink and fade
        modalCard.style.transition = 'all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        modalCard.style.transform = 'scale(0.8)';
        modalCard.style.opacity = '0';
        
        // Wait for animation to complete before hiding modal
        setTimeout(() => {
            modal.classList.remove('show');
            // Reset styles for next opening
            modalCard.style.transform = '';
            modalCard.style.opacity = '';
            modalCard.style.transition = '';
        }, 300);
    }
    
    // Station Edit Functions
    function openStationEditModal() {
        const modalCard = document.getElementById('stationModalCard');
        const stationName = modalCard.dataset.stationName;
        
        if (!stationName) return;
        
        // Switch from view mode to edit mode
        document.getElementById('stationViewContent').style.display = 'none';
        document.getElementById('stationEditContent').style.display = 'block';
        
        // Load station data for editing
        loadStationForEdit(stationName);
    }
    
    async function loadStationForEdit(stationName) {
        try {
            const response = await fetch(`/api/stations/${encodeURIComponent(stationName)}`);
            if (response.ok) {
                const stationData = await response.json();
                const station = stationData.station;
                
                // Populate form fields
                document.getElementById('editStationId').value = station.id || '';
                document.getElementById('editStationName').value = station.name || '';
                document.getElementById('editStationAltName').value = station.alt_name || '';
                document.getElementById('editStationDescription').value = station.description || '';
                document.getElementById('editStationSymbol').value = station.symbol || 'train';
                document.getElementById('editStationType').value = station.type || 'public';
                document.getElementById('editStationStatus').value = station.status || 'open';
                document.getElementById('editStationPlatforms').value = station.platform_count || '';
                
                // Show current image if exists
                if (station.image_path && station.image_path !== '') {
                    const preview = document.getElementById('currentImagePreview');
                    const img = document.getElementById('currentImage');
                    img.src = station.image_path;
                    preview.style.display = 'block';
                } else {
                    document.getElementById('currentImagePreview').style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Failed to load station for editing:', error);
        }
    }
    
    function closeStationEditModal() {
        // Switch back from edit mode to view mode
        document.getElementById('stationEditContent').style.display = 'none';
        document.getElementById('stationViewContent').style.display = 'block';
        
        // Reset form
        document.getElementById('stationEditForm').reset();
        document.getElementById('currentImagePreview').style.display = 'none';
    }
    
    async function saveStationChanges(event) {
        event.preventDefault();
        
        const form = document.getElementById('stationEditForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/api/stations/update', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Switch back to view mode
                    closeStationEditModal();
                    
                    // Show success message
                    alert('Station updated successfully!');
                    
                    // Reload the page to reflect changes
                    window.location.reload();
                } else {
                    alert('Error: ' + result.error);
                }
            } else {
                alert('Failed to update station. Please try again.');
            }
        } catch (error) {
            console.error('Error updating station:', error);
            alert('An error occurred while updating the station.');
        }
    }
    
    // Close modal event listeners
    document.getElementById('closeStationModal').addEventListener('click', closeStationModal);
    document.querySelector('.station-modal-backdrop').addEventListener('click', closeStationModal);
    document.getElementById('editStationModal').addEventListener('click', openStationEditModal);
    
    // Edit modal event listeners
    document.getElementById('cancelStationEdit').addEventListener('click', closeStationEditModal);
    document.getElementById('stationEditForm').addEventListener('submit', saveStationChanges);
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (document.getElementById('stationModal').classList.contains('show')) {
                if (document.getElementById('stationEditContent').style.display === 'block') {
                    closeStationEditModal();
                } else {
                    closeStationModal();
                }
            } else if (document.getElementById('addStationModal').classList.contains('show')) {
                closeAddStationModal();
            }
        }
    });

    function animateStats() {
        const statNumbers = document.querySelectorAll('.stat-number');
        statNumbers.forEach(stat => {
            const target = parseInt(stat.textContent);
            let current = 0;
            const increment = target / 50;
            
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    stat.textContent = target;
                    clearInterval(timer);
                } else {
                    stat.textContent = Math.floor(current);
                }
            }, 30);
        });
    }

    setTimeout(animateStats, 500);

    // Station Sorting Functions
    let sortOrder = 'default'; // 'default', 'asc', 'desc'
    let originalStationOrder = [];
    
    function initializeSorting() {
        // Store original order of stations
        const stationCards = Array.from(document.querySelectorAll('.station-card'));
        originalStationOrder = stationCards.map(card => ({
            element: card.cloneNode(true),
            name: card.dataset.name
        }));
    }
    
    function sortStations() {
        const stationsGrid = document.getElementById('stationsGrid');
        const stationCards = Array.from(stationsGrid.querySelectorAll('.station-card'));
        const sortBtn = document.getElementById('sortStationsBtn');
        const sortIcon = sortBtn.querySelector('.sort-icon');
        const sortText = sortBtn.querySelector('.sort-text');
        
        // Cycle through sort states: default -> asc -> desc -> default
        switch (sortOrder) {
            case 'default':
                // Sort A-Z
                stationCards.sort((a, b) => {
                    return a.dataset.name.localeCompare(b.dataset.name, 'de', { numeric: true });
                });
                sortOrder = 'asc';
                sortBtn.classList.add('active');
                sortBtn.classList.remove('reverse');
                sortIcon.textContent = 'sort_by_alpha';
                sortText.textContent = 'A-Z';
                break;
                
            case 'asc':
                // Sort Z-A
                stationCards.sort((a, b) => {
                    return b.dataset.name.localeCompare(a.dataset.name, 'de', { numeric: true });
                });
                sortOrder = 'desc';
                sortBtn.classList.add('active', 'reverse');
                sortIcon.textContent = 'sort_by_alpha';
                sortText.textContent = 'Z-A';
                break;
                
            case 'desc':
                // Reset to original order
                restoreOriginalOrder();
                sortOrder = 'default';
                sortBtn.classList.remove('active', 'reverse');
                sortIcon.textContent = 'sort_by_alpha';
                sortText.textContent = 'Sort A-Z';
                return;
        }
        
        // Clear and re-append sorted stations
        stationsGrid.innerHTML = '';
        stationCards.forEach(card => {
            stationsGrid.appendChild(card);
        });
        
        // Add smooth animation
        stationCards.forEach((card, index) => {
            card.style.animation = `slideInSort 0.3s ease-out ${index * 0.05}s both`;
        });
    }
    
    function restoreOriginalOrder() {
        const stationsGrid = document.getElementById('stationsGrid');
        stationsGrid.innerHTML = '';
        
        originalStationOrder.forEach((stationData, index) => {
            const newCard = stationData.element.cloneNode(true);
            
            // Re-attach event listeners for the restored cards
            newCard.addEventListener('click', function() {
                const stationName = this.dataset.name;
                openStationModal(this, stationName);
            });
            
            stationsGrid.appendChild(newCard);
            newCard.style.animation = `slideInSort 0.3s ease-out ${index * 0.05}s both`;
        });
    }
    
    // Initialize sorting when page loads
    initializeSorting();
    
    // Sort button event listener
    const sortStationsBtn = document.getElementById('sortStationsBtn');
    if (sortStationsBtn) {
        sortStationsBtn.addEventListener('click', sortStations);
    }
    
    // List View Functions
    let isListView = false;
    
    function toggleListView() {
        const stationsGrid = document.getElementById('stationsGrid');
        const stationsListView = document.getElementById('stationsListView');
        const listViewBtn = document.getElementById('listViewBtn');
        const listIcon = listViewBtn.querySelector('.material-symbols');
        const listText = listViewBtn.querySelector('.sort-text');
        
        if (!isListView) {
            // Switch to list view
            stationsGrid.style.display = 'none';
            stationsListView.style.display = 'block';
            generateAlphabeticalList();
            
            listViewBtn.classList.add('active');
            listIcon.textContent = 'grid_view';
            listText.textContent = 'Grid View';
            isListView = true;
        } else {
            // Switch back to grid view
            stationsGrid.style.display = 'grid';
            stationsListView.style.display = 'none';
            
            listViewBtn.classList.remove('active');
            listIcon.textContent = 'view_list';
            listText.textContent = 'List View';
            isListView = false;
        }
    }
    
    function generateAlphabeticalList() {
        const stationsListView = document.getElementById('stationsListView');
        const alphabetContainer = stationsListView.querySelector('.alphabet-container');
        const stationCards = Array.from(document.querySelectorAll('.station-card'));
        
        // Clear existing content
        alphabetContainer.innerHTML = '';
        
        // Group stations by first letter
        const stationsByLetter = {};
        
        stationCards.forEach(card => {
            const stationName = card.dataset.name;
            const firstLetter = stationName.charAt(0).toUpperCase();
            
            // Check if it's a letter or number/special character
            const letter = /[A-Z]/.test(firstLetter) ? firstLetter : '#';
            
            if (!stationsByLetter[letter]) {
                stationsByLetter[letter] = [];
            }
            
            // Extract station data
            const stationData = {
                name: stationName,
                altName: card.querySelector('.station-alt-name')?.textContent || '',
                description: card.querySelector('.station-info')?.textContent || '',
                icon: card.querySelector('.material-symbols')?.textContent || 'train',
                status: card.querySelector('.station-status')?.innerHTML || '',
                element: card
            };
            
            stationsByLetter[letter].push(stationData);
        });
        
        // Sort letters (# comes last)
        const sortedLetters = Object.keys(stationsByLetter).sort((a, b) => {
            if (a === '#') return 1;
            if (b === '#') return -1;
            return a.localeCompare(b);
        });
        
        // Generate HTML for each letter section
        sortedLetters.forEach(letter => {
            const stations = stationsByLetter[letter];
            
            // Sort stations within the letter group
            stations.sort((a, b) => a.name.localeCompare(b.name, 'de', { numeric: true }));
            
            const sectionHTML = `
                <div class="alphabet-section">
                    <div class="alphabet-header" data-letter="${letter}">
                        ${letter === '#' ? 'Numbers & Symbols' : letter}
                    </div>
                    <div class="alphabet-stations">
                        ${stations.map(station => `
                            <div class="list-station-item" data-name="${station.name}">
                                <div class="list-station-icon">
                                    <span class="material-symbols">${station.icon}</span>
                                </div>
                                <div class="list-station-content">
                                    <div class="list-station-name">${station.name}</div>
                                    ${station.altName ? `<div class="list-station-alt-name">${station.altName}</div>` : ''}
                                    ${station.description ? `<div class="list-station-description">${station.description}</div>` : ''}
                                    <div class="list-station-status">${station.status}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            alphabetContainer.insertAdjacentHTML('beforeend', sectionHTML);
        });
        
        // Add click event listeners to list items
        const listItems = alphabetContainer.querySelectorAll('.list-station-item');
        listItems.forEach(item => {
            item.addEventListener('click', function() {
                const stationName = this.dataset.name;
                const originalCard = stationCards.find(card => card.dataset.name === stationName);
                if (originalCard) {
                    openStationModal(originalCard, stationName);
                }
            });
        });
        
        // Add smooth animation
        const sections = alphabetContainer.querySelectorAll('.alphabet-section');
        sections.forEach((section, index) => {
            section.style.animation = `slideInSort 0.4s ease-out ${index * 0.1}s both`;
        });
    }
    
    // List view button event listener
    const listViewBtn = document.getElementById('listViewBtn');
    if (listViewBtn) {
        listViewBtn.addEventListener('click', toggleListView);
    }

    // Add Station Modal Functions
    function openAddStationModal() {
        const modal = document.getElementById('addStationModal');
        const modalCard = modal.querySelector('.station-modal-card');
        
        // Set initial state - small and centered (GNOME style)
        modalCard.style.transform = 'translate(-50%, -50%) scale(0.6)';
        modalCard.style.opacity = '0';
        modalCard.style.transition = 'all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        
        // Show modal
        modal.classList.add('show');
        
        // Animate to full size with GNOME-style bounce
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                modalCard.style.transform = 'translate(-50%, -50%) scale(1.02)';
                modalCard.style.opacity = '1';
                
                // Second bounce phase
                setTimeout(() => {
                    modalCard.style.transition = 'transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                    modalCard.style.transform = 'translate(-50%, -50%) scale(1)';
                }, 400);
            });
        });
    }
    
    function closeAddStationModal() {
        const modal = document.getElementById('addStationModal');
        const modalCard = modal.querySelector('.station-modal-card');
        
        // GNOME-style close animation - shrink and fade
        modalCard.style.transition = 'all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        modalCard.style.transform = 'translate(-50%, -50%) scale(0.8)';
        modalCard.style.opacity = '0';
        
        // Wait for animation to complete before hiding modal
        setTimeout(() => {
            modal.classList.remove('show');
            // Reset form
            document.getElementById('addStationForm').reset();
            // Reset styles for next opening
            modalCard.style.transform = '';
            modalCard.style.opacity = '';
            modalCard.style.transition = '';
        }, 300);
    }
    
    async function saveNewStation(event) {
        event.preventDefault();
        
        const form = document.getElementById('addStationForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/api/stations/create', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // Close modal
                    closeAddStationModal();
                    
                    // Show success message
                    alert('Station created successfully!');
                    
                    // Reload page to show new station
                    window.location.reload();
                } else {
                    alert('Failed to create station: ' + (result.error || 'Unknown error'));
                }
            } else {
                alert('Failed to create station. Please try again.');
            }
        } catch (error) {
            console.error('Error creating station:', error);
            alert('An error occurred while creating the station.');
        }
    }
    
    // Add Station Event Listeners
    const addStationBtn = document.getElementById('addStationBtn');
    if (addStationBtn) {
        addStationBtn.addEventListener('click', openAddStationModal);
    }
    
    const closeAddStationModalBtn = document.getElementById('closeAddStationModal');
    if (closeAddStationModalBtn) {
        closeAddStationModalBtn.addEventListener('click', closeAddStationModal);
    }
    
    const cancelAddStationBtn = document.getElementById('cancelAddStation');
    if (cancelAddStationBtn) {
        cancelAddStationBtn.addEventListener('click', closeAddStationModal);
    }
    
    const addStationForm = document.getElementById('addStationForm');
    if (addStationForm) {
        addStationForm.addEventListener('submit', saveNewStation);
    }
    
    // Add backdrop click for add station modal
    const addStationBackdrop = document.querySelector('#addStationModal .station-modal-backdrop');
    if (addStationBackdrop) {
        addStationBackdrop.addEventListener('click', closeAddStationModal);
    }
});

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideInSort {
        from {
            transform: translateY(20px) scale(0.9);
            opacity: 0;
        }
        to {
            transform: translateY(0) scale(1);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);