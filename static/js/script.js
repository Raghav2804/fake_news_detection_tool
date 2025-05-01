// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Tab Navigation
    const tabButtons = document.querySelectorAll('#input-tabs button');
    const tabPanels = document.querySelectorAll('.tab-panel');

    // Analysis Buttons
    const analyzeTextBtn = document.getElementById('analyze-text-btn');
    const analyzeUrlBtn = document.getElementById('analyze-url-btn');
    const analyzeImageBtn = document.getElementById('analyze-image-btn');

    // Input Elements
    const newsTextInput = document.getElementById('news-text');
    const newsUrlInput = document.getElementById('news-url');
    const newsImageInput = document.getElementById('news-image');

    // Results Section
    const resultsSection = document.getElementById('results-section');
    const predictionIcon = document.getElementById('prediction-icon');
    const predictionLabel = document.getElementById('prediction-label');
    const confidenceScore = document.getElementById('confidence-score');
    const contentPreview = document.getElementById('content-preview');
    const sourceUrlContainer = document.getElementById('source-url');
    const sourceUrlLink = document.querySelector('#source-url a');

    // Image Preview
    const imagePreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');

    // Trending News
    const trendingNewsContainer = document.getElementById('trending-news');
    const refreshNewsBtn = document.getElementById('refresh-news-btn');

    // Modal
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    const closeModalBtn = document.getElementById('close-modal');

    // Loading Overlay
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');

    // Other Buttons
    const aboutBtn = document.getElementById('about-btn');
    const disclaimerBtn = document.getElementById('disclaimer-btn');
    const viewResultsBtn = document.createElement('button');
    viewResultsBtn.innerHTML = '<i class="fas fa-history mr-1"></i>View History';
    viewResultsBtn.className = 'hover:text-blue-400';
    viewResultsBtn.id = 'view-results-btn';

    // Add the view results button to the footer
    document.querySelector('.flex.space-x-4').prepend(viewResultsBtn);

    // Tab Navigation
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Deactivate all tabs
            tabButtons.forEach(btn => {
                btn.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600');
                btn.classList.add('text-gray-500', 'hover:text-gray-600', 'hover:border-gray-300');
            });

            // Activate selected tab
            button.classList.remove('text-gray-500', 'hover:text-gray-600', 'hover:border-gray-300');
            button.classList.add('text-blue-600', 'border-b-2', 'border-blue-600');

            // Hide all tab panels
            tabPanels.forEach(panel => {
                panel.classList.add('hidden');
                panel.classList.remove('active');
            });

            // Show selected tab panel
            const tabId = button.getAttribute('data-tab');
            const tabPanel = document.getElementById(tabId);
            tabPanel.classList.remove('hidden');
            tabPanel.classList.add('active');
        });
    });

    // Text Analysis
    analyzeTextBtn.addEventListener('click', () => {
        const text = newsTextInput.value.trim();

        if (!text) {
            showError('Please enter some text to analyze.');
            return;
        }

        showLoading('Analyzing text...');

        fetch('/text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error analyzing text');
                });
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            displayResults(data);
        })
        .catch(error => {
            hideLoading();
            showError(error.message);
        });
    });

    // URL Analysis
    analyzeUrlBtn.addEventListener('click', () => {
        const url = newsUrlInput.value.trim();

        if (!url) {
            showError('Please enter a URL to analyze.');
            return;
        }

        if (!isValidUrl(url)) {
            showError('Please enter a valid URL.');
            return;
        }

        showLoading('Fetching and analyzing URL content...');

        fetch('/url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error analyzing URL');
                });
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            displayResults(data);

            // Show source URL link
            sourceUrlContainer.classList.remove('hidden');
            sourceUrlLink.href = url;
        })
        .catch(error => {
            hideLoading();
            showError(error.message);
        });
    });

    // Image Analysis
    newsImageInput.addEventListener('change', () => {
        const file = newsImageInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                imagePreview.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }
    });

    analyzeImageBtn.addEventListener('click', () => {
        const file = newsImageInput.files[0];

        if (!file) {
            showError('Please select an image to analyze.');
            return;
        }

        showLoading('Processing image and extracting text...');

        const formData = new FormData();
        formData.append('image', file);

        fetch('/image', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error analyzing image');
                });
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            displayResults(data);
        })
        .catch(error => {
            hideLoading();
            showError(error.message);
        });
    });

    // Fetch Trending News
    function fetchTrendingNews() {
        trendingNewsContainer.innerHTML = `
            <div class="col-span-full flex justify-center items-center p-8">
                <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        `;

        fetch('/trending')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch trending news');
                }
                return response.json();
            })
            .then(news => {
                displayTrendingNews(news);
            })
            .catch(error => {
                trendingNewsContainer.innerHTML = `
                    <div class="col-span-full p-4 text-center text-gray-600">
                        <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                        <p>Failed to load trending news. Please try again later.</p>
                        <button id="retry-news-btn" class="mt-2 text-blue-600 hover:text-blue-800">
                            <i class="fas fa-redo mr-1"></i>Retry
                        </button>
                    </div>
                `;

                document.getElementById('retry-news-btn').addEventListener('click', fetchTrendingNews);
            });
    }

    function displayTrendingNews(news) {
        if (!news || news.length === 0) {
            trendingNewsContainer.innerHTML = `
                <div class="col-span-full p-4 text-center text-gray-600">
                    <p>No trending news available at the moment.</p>
                </div>
            `;
            return;
        }

        trendingNewsContainer.innerHTML = '';

        news.forEach(article => {
            const card = document.createElement('div');
            card.className = 'news-card border rounded-lg overflow-hidden shadow-sm hover:shadow-md';

            const imageUrl = article.image_url || 'https://via.placeholder.com/300x200?text=No+Image';

            card.innerHTML = `
                <div class="aspect-w-16 aspect-h-9 bg-gray-100">
                    <img src="${imageUrl}" alt="${article.title}" 
                        class="w-full h-48 object-cover" 
                        onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
                </div>
                <div class="p-4">
                    <div class="flex justify-between items-start mb-2">
                        <h3 class="text-lg font-semibold line-clamp-2">${article.title}</h3>
                        <button class="verify-news-btn text-blue-600 hover:text-blue-800 ml-2 flex-shrink-0" 
                                data-url="${article.url}" title="Verify this news">
                            <i class="fas fa-check-circle"></i>
                        </button>
                    </div>
                    <p class="text-gray-600 text-sm line-clamp-3 mb-2">${article.description || 'No description available'}</p>
                    <div class="flex justify-between items-center text-xs text-gray-500">
                        <span>${article.source || 'Unknown source'}</span>
                        <a href="${article.url}" target="_blank" class="text-blue-600 hover:underline" rel="noopener noreferrer">
                            Read More
                        </a>
                    </div>
                </div>
            `;

            trendingNewsContainer.appendChild(card);

            // Add event listener to verify button
            const verifyBtn = card.querySelector('.verify-news-btn');
            verifyBtn.addEventListener('click', () => {
                const url = verifyBtn.getAttribute('data-url');
                if (url) {
                    // Switch to URL tab and populate field
                    document.getElementById('url-tab').click();
                    newsUrlInput.value = url;

                    // Scroll to input section
                    document.querySelector('main').scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    // Refresh trending news
    refreshNewsBtn.addEventListener('click', fetchTrendingNews);

    // Modal functions
    function showModal(title, content) {
        modalTitle.textContent = title;
        modalContent.innerHTML = content;
        modal.classList.remove('hidden');
    }

    function hideModal() {
        modal.classList.add('hidden');
    }

    closeModalBtn.addEventListener('click', hideModal);

    // Close modal when clicking outside
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            hideModal();
        }
    });

    // About and Disclaimer modals
    aboutBtn.addEventListener('click', () => {
        showModal('About Fake News Detector', `
            <p class="mb-4">The Fake News Detector is an AI-powered tool designed to help identify potentially false information in news articles.</p>
            <p class="mb-4">Using machine learning algorithms, the system analyzes text patterns, writing style, and content indicators to determine the likelihood that a news article contains false information.</p>
            <p class="mb-4">Key features include:</p>
            <ul class="list-disc ml-6 mb-4">
                <li>Text analysis of pasted content</li>
                <li>URL scraping and analysis</li>
                <li>Image-to-text extraction and analysis</li>
                <li>Real-time trending news integration</li>
            </ul>
            <p>This tool is intended for educational purposes and should be used as one of many resources to evaluate news credibility.</p>
        `);
    });

    disclaimerBtn.addEventListener('click', () => {
        showModal('Disclaimer', `
            <p class="mb-4">This Fake News Detection tool provides an automated analysis based on machine learning algorithms and should not be considered definitive or infallible.</p>
            <p class="mb-4">The predictions made by this system are based on patterns it has learned from training data and may not accurately identify all instances of false information. False positives and false negatives are possible.</p>
            <p class="mb-4">Users should:</p>
            <ul class="list-disc ml-6 mb-4">
                <li>Use this tool as just one of several methods to evaluate news credibility</li>
                <li>Verify information through trusted sources</li>
                <li>Consider the context and source of information</li>
                <li>Exercise critical thinking when consuming news</li>
            </ul>
            <p class="mb-4">The developers of this tool are not responsible for any decisions made based on its predictions or any consequences thereof.</p>
            <p>By using this tool, you acknowledge that you understand these limitations.</p>
        `);
    });

    // Loading overlay functions
    function showLoading(message) {
        loadingMessage.textContent = message || 'Loading...';
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }

    // Error handling
    function showError(message) {
        showModal('Error', `
            <div class="text-red-600 mb-4">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                ${message}
            </div>
        `);
    }

    // Display results
    function displayResults(data) {
        // Set prediction icon and class
        let iconClass, resultClass, label;

        if (data.prediction === 'real') {
            iconClass = 'fas fa-check-circle text-green-500';
            resultClass = 'prediction-real';
            label = 'REAL NEWS';
        } else if (data.prediction === 'fake') {
            iconClass = 'fas fa-times-circle text-red-500';
            resultClass = 'prediction-fake';
            label = 'FAKE NEWS';
        } else {
            iconClass = 'fas fa-question-circle text-gray-500';
            resultClass = 'prediction-unknown';
            label = 'UNCERTAIN';
        }

        // Update prediction display
        predictionIcon.className = iconClass;
        predictionLabel.textContent = label;
        confidenceScore.textContent = `Confidence: ${data.confidence}%`;

        // Set result box class
        const resultBox = document.getElementById('prediction-result');
        resultBox.className = `flex items-center justify-center p-4 rounded-lg ${resultClass}`;

        // Update content preview
        if (data.extracted_text) {
            contentPreview.textContent = data.extracted_text;
        } else if (data.original_text) {
            contentPreview.textContent = data.original_text;
        } else {
            contentPreview.textContent = 'No content preview available.';
        }

        // Show/hide source URL
        if (data.source_url) {
            sourceUrlContainer.classList.remove('hidden');
            sourceUrlLink.href = data.source_url;
        } else {
            sourceUrlContainer.classList.add('hidden');
        }

        // Show results section
        resultsSection.classList.remove('hidden');

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Helper function to validate URL
    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    // View Results History
    viewResultsBtn.addEventListener('click', () => {
        showLoading('Loading prediction history...');

        fetch('/results')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch results history');
                }
                return response.json();
            })
            .then(results => {
                hideLoading();
                displayResultsHistory(results);
            })
            .catch(error => {
                hideLoading();
                showError('Failed to load prediction history: ' + error.message);
            });
    });

    function displayResultsHistory(results) {
        if (!results || results.length === 0) {
            showModal('Prediction History', '<p class="text-gray-600">No prediction history available yet.</p>');
            return;
        }

        // Create table with results
        let tableHtml = `
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white border border-gray-200">
                    <thead>
                        <tr>
                            <th class="px-4 py-2 border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                            <th class="px-4 py-2 border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                            <th class="px-4 py-2 border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prediction</th>
                            <th class="px-4 py-2 border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                            <th class="px-4 py-2 border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Preview</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        // Add rows for each result, most recent first
        results.reverse().slice(0, 20).forEach(result => {
            const predictionClass = result.prediction === 'real' ? 'text-green-600' : 'text-red-600';

            tableHtml += `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-2 border-b border-gray-200 text-sm">${result.timestamp}</td>
                    <td class="px-4 py-2 border-b border-gray-200 text-sm">${result.input_type}</td>
                    <td class="px-4 py-2 border-b border-gray-200 text-sm font-medium ${predictionClass}">${result.prediction.toUpperCase()}</td>
                    <td class="px-4 py-2 border-b border-gray-200 text-sm">${result.confidence}%</td>
                    <td class="px-4 py-2 border-b border-gray-200 text-sm">
            `;

            // Add appropriate content based on type
            if (result.input_type === 'image' && result.image_path) {
                tableHtml += `<a href="${result.image_path}" target="_blank" class="text-blue-600 hover:underline">View Image</a>`;
            } else if (result.input_type === 'url' && result.source_url) {
                tableHtml += `
                    <div class="truncate max-w-xs" title="${result.content_preview}">
                        ${result.content_preview.substring(0, 50)}...
                    </div>
                    <a href="${result.source_url}" target="_blank" class="text-blue-600 hover:underline text-xs">View Source</a>
                `;
            } else {
                tableHtml += `
                    <div class="truncate max-w-xs" title="${result.content_preview}">
                        ${result.content_preview.substring(0, 50)}...
                    </div>
                `;
            }

            tableHtml += `
                    </td>
                </tr>
            `;
        });

        tableHtml += `
                    </tbody>
                </table>
            </div>
            <p class="mt-4 text-xs text-gray-500">
                Showing latest ${Math.min(results.length, 20)} of ${results.length} results.
                <br>Results are stored in <code>static/results/prediction_results.csv</code>
                <br>Processed images are saved in <code>static/results/processed_images/</code>
            </p>
        `;

        showModal('Prediction History', tableHtml);
    }

    // Initialize - fetch trending news on page load
    fetchTrendingNews();
});