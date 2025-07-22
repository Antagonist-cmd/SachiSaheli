document.addEventListener("DOMContentLoaded", function() {
    
    // Global chart instance
    let moodChartInstance = null;
    
    // Chart configuration
    const chartConfig = {
        defaultTimeRange: 30,
        interpolation: true,
        clickablePoints: true
    };
    
    // Initialize mood chart system
    initMoodChartSystem();
    
    function initMoodChartSystem() {
        // Validate requirements
        if (!validateChartRequirements()) return;
        
        // Setup event listeners
        setupChartControls();
        
        // Load initial chart
        loadMoodChart(chartConfig.defaultTimeRange);
    }
    
    function validateChartRequirements() {
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js library not loaded');
            showError('Chart library not available');
            return false;
        }
        
        if (!document.getElementById("moodChart")) {
            console.error('❌ Canvas element #moodChart not found');
            return false;
        }
        
        return true;
    }
    
    function setupChartControls() {
        // Time range selector
        const timeSelector = document.getElementById("timeRangeSelector");
        if (timeSelector) {
            timeSelector.addEventListener("change", function() {
                const range = this.value;
                loadMoodChart(range);
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById("refreshChart");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", function() {
                const currentRange = timeSelector ? timeSelector.value : chartConfig.defaultTimeRange;
                loadMoodChart(currentRange, true);
            });
        }
    }
    
    async function loadMoodChart(timeRange, forceRefresh = false) {
        showLoading(true);
        
        try {
            let chartData;
            
            if (forceRefresh) {
                // Fetch fresh data from server
                chartData = await fetchChartData(timeRange);
            } else {
                // Use embedded data or fetch if needed
                chartData = getEmbeddedChartData(timeRange);
                if (!chartData) {
                    chartData = await fetchChartData(timeRange);
                }
            }
            
            if (!chartData || chartData.labels.length === 0) {
                showEmptyState();
                return;
            }
            
            renderMoodChart(chartData);
            updateChartInfo(chartData, timeRange);
            
        } catch (error) {
            console.error('❌ Error loading mood chart:', error);
            showError('Failed to load mood chart data');
        } finally {
            showLoading(false);
        }
    }
    
    function getEmbeddedChartData(timeRange) {
        const moodDataEl = document.getElementById("moodData");
        if (!moodDataEl) return null;
        
        try {
            const moods = JSON.parse(moodDataEl.textContent);
            return processMoodsForChart(moods, timeRange);
        } catch (e) {
            console.error('Error parsing embedded mood data:', e);
            return null;
        }
    }
    
    async function fetchChartData(timeRange) {
        const response = await fetch(`/api/mood/chart-data?range=${timeRange}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || 'Failed to fetch chart data');
        }
        
        return result.data;
    }
    
    function processMoodsForChart(moods, timeRange) {
        if (!moods || moods.length === 0) {
            return { labels: [], data: [], moods: [], interpolated: [] };
        }
        
        // Filter by time range
        let filteredMoods = moods;
        if (timeRange !== 'all') {
            const days = parseInt(timeRange);
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - days);
            
            filteredMoods = moods.filter(mood => {
                const moodDate = new Date(mood.timestamp);
                return moodDate >= cutoffDate;
            });
        }
        
        // Process moods
        const processedMoods = filteredMoods.map(mood => {
            const ts = new Date(mood.timestamp);
            return {
                ...mood,
                timestamp_obj: ts,
                date_key: ts.toISOString().split('T')[0],
                simple_mood: getMoodFromTags(mood.diagnosis_tags || [])
            };
        });
        
        // Sort by timestamp
        processedMoods.sort((a, b) => a.timestamp_obj - b.timestamp_obj);
        
        // Group by date (latest mood per day)
        const dailyMoods = {};
        processedMoods.forEach(mood => {
            const dateKey = mood.date_key;
            if (!dailyMoods[dateKey] || mood.timestamp_obj > dailyMoods[dateKey].timestamp_obj) {
                dailyMoods[dateKey] = mood;
            }
        });
        
        // Convert to chart format
        const sortedDates = Object.keys(dailyMoods).sort();
        const labels = [];
        const data = [];
        const moodEntries = [];
        const interpolated = [];
        
        sortedDates.forEach(dateKey => {
            const mood = dailyMoods[dateKey];
            const date = new Date(dateKey);
            const label = date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
            });
            
            labels.push(label);
            data.push(convertMoodToScore(mood.simple_mood));
            moodEntries.push(mood);
            interpolated.push(false);
        });
        
        return { labels, data, moods: moodEntries, interpolated };
    }
    
    function getMoodFromTags(tags) {
        if (!tags || tags.length === 0) return "Neutral";
        
        // Convert tags to lowercase for comparison
        const lowerTags = tags.map(t => String(t).toLowerCase().trim());
        
        // Very Sad
        if (lowerTags.some(t => ['depression', 'suicidal thoughts', 'suicidal_thoughts', 'hopelessness'].includes(t))) {
            return "Very Sad";
        }
        
        // Sad  
        if (lowerTags.some(t => ['anxiety', 'burnout', 'stress', 'low motivation', 'low_motivation', 'insomnia'].includes(t))) {
            return "Sad";
        }
        
        // Very Happy
        if (lowerTags.some(t => ['very happy', 'very_happy', 'gratitude', 'joy', 'excited'].includes(t))) {
            return "Very Happy";
        }
        
        // Happy
        if (lowerTags.some(t => ['healthy', 'motivated', 'balanced', 'stable', 'calm'].includes(t))) {
            return "Happy";
        }
        
        return "Neutral";
    }
    
    function convertMoodToScore(mood) {
        const scores = {
            "Very Sad": 1,
            "Sad": 2,
            "Neutral": 3,
            "Happy": 4,
            "Very Happy": 5
        };
        return scores[mood] || 3;
    }
    
    function renderMoodChart(chartData) {
        const canvas = document.getElementById("moodChart");
        const ctx = canvas.getContext("2d");
        
        // Destroy existing chart
        if (moodChartInstance) {
            moodChartInstance.destroy();
            moodChartInstance = null;
        }
        
        moodChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Mood Trend',
                    data: chartData.data,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#4f46e5',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Your Mood Journey',
                        font: {
                            size: 18,
                            weight: '600'
                        },
                        color: '#1f2937',
                        padding: { top: 10, bottom: 20 }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13 },
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return `${context[0].label}`;
                            },
                            label: function(context) {
                                const moodLabels = ['', 'Very Sad', 'Sad', 'Neutral', 'Happy', 'Very Happy'];
                                const mood = chartData.moods[context.dataIndex];
                                
                                const lines = [
                                    `Mood: ${moodLabels[context.raw]}`,
                                    `Time: ${mood.timestamp_display || new Date(mood.timestamp).toLocaleString()}`
                                ];
                                
                                if (mood.diagnosis_tags && mood.diagnosis_tags.length > 0) {
                                    lines.push(`Tags: ${mood.diagnosis_tags.join(', ')}`);
                                }
                                
                                if (mood.journal_entry) {
                                    lines.push(`Journal: ${mood.journal_entry.substring(0, 50)}...`);
                                }
                                
                                return lines;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            color: '#6b7280',
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        min: 1,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                            color: '#6b7280',
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                const labels = ['', 'Very Sad', 'Sad', 'Neutral', 'Happy', 'Very Happy'];
                                return labels[value];
                            }
                        },
                        grid: {
                            color: 'rgba(107, 114, 128, 0.2)',
                            lineWidth: 1
                        }
                    }
                },
                onClick: function(event, elements) {
                    if (elements.length > 0 && chartConfig.clickablePoints) {
                        const pointIndex = elements[0].index;
                        const mood = chartData.moods[pointIndex];
                        handleChartPointClick(mood, pointIndex);
                    }
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                }
            }
        });
    }
    
    function handleChartPointClick(mood, index) {
        // Create modal or detailed view for clicked mood entry
        console.log('🎯 Clicked mood entry:', mood);
        
        // You can implement a modal here to show detailed mood information
        const modal = createMoodDetailModal(mood);
        document.body.appendChild(modal);
        modal.style.display = 'block';
        
        // Close modal after 5 seconds or on click
        setTimeout(() => {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
        }, 5000);
        
        modal.addEventListener('click', () => {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
        });
    }
    
    function createMoodDetailModal(mood) {
        const modal = document.createElement('div');
        modal.className = 'mood-detail-modal';
        modal.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: white; border-radius: 12px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            max-width: 400px; z-index: 1000; border: 2px solid #e5e7eb;
        `;
        
        modal.innerHTML = `
            <h4 style="margin: 0 0 15px 0; color: #1f2937;">📅 Mood Entry Details</h4>
            <p><strong>Date:</strong> ${mood.timestamp_display || new Date(mood.timestamp).toLocaleString()}</p>
            <p><strong>Mood:</strong> ${mood.simple_mood || 'Unknown'}</p>
            ${mood.diagnosis_tags && mood.diagnosis_tags.length > 0 ? 
                `<p><strong>Tags:</strong> ${mood.diagnosis_tags.join(', ')}</p>` : ''}
            ${mood.journal_entry ? 
                `<p><strong>Journal:</strong> ${mood.journal_entry.substring(0, 100)}${mood.journal_entry.length > 100 ? '...' : ''}</p>` : ''}
            <button style="margin-top: 15px; padding: 8px 16px; background: #6366f1; color: white; border: none; border-radius: 6px; cursor: pointer;">Close</button>
        `;
        
        return modal;
    }
    
    function updateChartInfo(chartData, timeRange) {
        const countEl = document.getElementById("dataPointCount");
        const rangeEl = document.getElementById("dateRange");
        
        if (countEl) {
            countEl.textContent = `${chartData.data.length} data points`;
        }
        
        if (rangeEl && chartData.labels.length > 0) {
            const firstLabel = chartData.labels[0];
            const lastLabel = chartData.labels[chartData.labels.length - 1];
            rangeEl.textContent = `${firstLabel} - ${lastLabel}`;
        }
    }
    
    function showLoading(show) {
        const loadingEl = document.getElementById("chartLoading");
        const chartEl = document.getElementById("moodChart");
        const emptyEl = document.getElementById("emptyChart");
        
        if (loadingEl) loadingEl.style.display = show ? 'block' : 'none';
        if (chartEl) chartEl.style.display = show ? 'none' : 'block';
        if (emptyEl) emptyEl.style.display = 'none';
    }
    
    function showEmptyState() {
        const loadingEl = document.getElementById("chartLoading");
        const chartEl = document.getElementById("moodChart");
        const emptyEl = document.getElementById("emptyChart");
        
        if (loadingEl) loadingEl.style.display = 'none';
        if (chartEl) chartEl.style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'block';
    }
    
    function showError(message) {
        console.error('Chart error:', message);
        // You can implement error UI here
    }
});
