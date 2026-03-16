# Copyright 2025 Google LLC

WEATHER_WIDGET_HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 16px; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: transparent; }
        .weather-card {
            background: linear-gradient(135deg, #0ba360 0%, #32b57e 50%, #3cba92 100%);
            border-radius: 20px;
            padding: 24px;
            color: white;
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            gap: 16px;
            max-width: 400px;
            margin: 0 auto;
            position: relative;
            overflow: hidden;
        }
        .weather-card::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
            pointer-events: none;
        }
        .header { display: flex; justify-content: space-between; align-items: flex-start; z-index: 1; }
        .location { font-size: 26px; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
        .condition { font-size: 16px; opacity: 0.9; margin: 4px 0 0 0; text-transform: capitalize; font-weight: 500; }
        .temp-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; z-index: 1; margin: 10px 0; }
        .temp { font-size: 64px; font-weight: 800; margin: 0; line-height: 1; letter-spacing: -2px;}
        .main-icon { width: 80px; height: 80px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1)); }
        .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 8px; z-index: 1; }
        .detail-item { background: rgba(0,0,0,0.1); padding: 14px; border-radius: 14px; backdrop-filter: blur(10px); }
        .detail-label { font-size: 12px; opacity: 0.8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        .detail-value { font-size: 18px; font-weight: 700; }
        .forecast { display: flex; justify-content: space-between; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2); z-index: 1; }
        .forecast-day { display: flex; flex-direction: column; align-items: center; gap: 10px; cursor: pointer; padding: 8px; border-radius: 12px; transition: background 0.2s; }
        .forecast-day:hover { background: rgba(255,255,255,0.1); }
        .forecast-icon { width: 28px; height: 28px; }
        .forecast-icon { width: 28px; height: 28px; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script>
        const getSVG = (iconType) => {
            const icons = {
                'sun': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>',
                'cloud': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path></svg>',
                'rain': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 13v8"></path><path d="M8 13v8"></path><path d="M12 15v8"></path><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"></path></svg>',
                'snow': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m20 17.5-8-4.5-8 4.5"></path><path d="m4 6.5 8 4.5 8-4.5"></path><path d="M12 22v-9"></path><path d="M12 2v9"></path></svg>',
                'storm': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m19 11-4-7-5 11h4l-3 7 10-14z"></path></svg>'
            };
            return icons[iconType] || icons['sun'];
        };

        const getBgGradient = (iconType) => {
            const gradients = {
                'sun': 'linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #FFB627 100%)',
                'cloud': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #4facfe 100%)',
                'rain': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'snow': 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
                'storm': 'linear-gradient(135deg, #f77062 0%, #fe5196 100%)'
            };
            return gradients[iconType] || 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)';
        };

        const getFontColor = (iconType) => {
            return (iconType === 'snow' || iconType === 'cloud') ? '#333' : 'white';
        };

        window.handleWeatherClick = function(index) {
            const data = window.__WEATHER_DATA__;
            if (!data || !data.forecast) return;
            const dayData = data.forecast[index];
            window.parent.postMessage({
                type: 'a2ui-action',
                detail: {
                    action: {
                        type: 'Action',
                        name: 'show_weather_details',
                        context: [
                            { key: 'location', value: { literalString: String(data.location || "Unknown") } },
                            { key: 'day', value: { literalString: String(dayData.day || "Day") } },
                            { key: 'high', value: { literalString: String(dayData.high || "--") } },
                            { key: 'condition', value: { literalString: String(dayData.icon || "sun") } }
                        ]
                    }
                }
            }, '*');
        };

        function render(data) {
            const root = document.getElementById('root');
            if (!data) {
                root.innerHTML = '<div style="padding: 24px; color: #666">Loading Weather...</div>';
                return;
            }
            window.__WEATHER_DATA__ = data;

            const location = data.location || "Unknown Location";
            const temp = data.temperature || "--";
            const condition = data.condition || "Unknown";
            const humidity = data.humidity || "--%";
            const wind = data.wind || "--";
            const mainIcon = data.icon || 'sun';
            
            const forecastList = data.forecast || [];
            let forecastHtml = '';
            
            if (forecastList.length > 0) {
                const daysHtml = forecastList.slice(0, 4).map((day, index) => {
                    const dayName = day.day || "Day";
                    const high = day.high || "--";
                    const dayIcon = day.icon || 'sun';
                    return `
                    <div class="forecast-day" onclick="handleWeatherClick(${index})">
                        <div style="font-size: 14px; opacity: 0.9">${dayName}</div>
                        <div class="forecast-icon">${getSVG(dayIcon)}</div>
                        <div style="font-weight: 700">${high}°</div>
                    </div>`;
                }).join('');
                forecastHtml = `<div class="forecast">${daysHtml}</div>`;
            }

            const bg = getBgGradient(mainIcon);
            const fontColor = getFontColor(mainIcon);
            const overlayClass = (mainIcon === 'snow' || mainIcon === 'cloud') ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.1)';

            root.innerHTML = `
                <div class="weather-card" style="background: ${bg}; color: ${fontColor}">
                    <div class="header">
                        <div>
                            <h2 class="location">${location}</h2>
                            <p class="condition">${condition}</p>
                        </div>
                    </div>
                    
                    <div class="temp-row">
                        <h1 class="temp">${temp}°</h1>
                        <div class="main-icon">${getSVG(mainIcon)}</div>
                    </div>

                    <div class="details-grid">
                        <div class="detail-item" style="background: ${overlayClass}">
                            <div class="detail-label">Humidity</div>
                            <div class="detail-value">${humidity}</div>
                        </div>
                        <div class="detail-item" style="background: ${overlayClass}">
                            <div class="detail-label">Wind</div>
                            <div class="detail-value">${wind}</div>
                        </div>
                    </div>

                    ${forecastHtml}
                </div>
            `;
        }

        const handler = (event) => {
            if (event.data && event.data.type === 'UPDATE_DATA') {
                render(event.data.data || event.data.widgetData);
            }
        };
        window.addEventListener('message', handler);
        window.parent.postMessage({ type: 'REQUEST_DATA' }, '*');
        
        render(null);
    </script>
</body>
</html>
"""

STOCKS_WIDGET_HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 16px; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: transparent; }
        .stocks-card {
            background: linear-gradient(180deg, #2b2b36 0%, #1e1e24 50%, #151519 100%);
            border-radius: 20px;
            padding: 24px;
            color: #f1f1f1;
            box-shadow: 0 12px 24px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 400px;
            margin: 0 auto;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .header { display: flex; justify-content: space-between; align-items: flex-start; }
        .symbol { font-size: 32px; font-weight: 800; margin: 0; letter-spacing: -1px; text-transform: uppercase; color: #fff;}
        .company { font-size: 14px; color: #a1a1aa; margin: 4px 0 0 0; font-weight: 500;}
        .price { font-size: 44px; font-weight: 800; margin: 0; line-height: 1; text-align: right; letter-spacing: -1px; color: #fff; }
        .change-pill { font-size: 16px; font-weight: 700; text-align: right; margin-top: 10px; display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 8px; }
        .change-pill.positive { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }
        .change-pill.negative { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); }
        .change-icon { width: 14px; height: 14px; }
        
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.08); }
        .stat-item { display: flex; flex-direction: column; gap: 6px; }
        .stat-label { font-size: 12px; color: #71717a; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        .stat-value { font-size: 16px; font-weight: 600; color: #e4e4e7; }
        
        .news-section { margin-top: 8px; display: flex; flex-direction: column; gap: 12px; }
        .news-header { font-size: 13px; color: #71717a; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; font-weight: 700; }
        .news-item { font-size: 14px; line-height: 1.5; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 10px; border-left: 3px solid #3b82f6; transition: background 0.2s; cursor: pointer; }
        .news-item:hover { background: rgba(255,255,255,0.08); }
    </style>
</head>
<body>
    <div id="root"></div>
    <script>
        window.handleStockClick = function(index) {
            const data = window.__STOCKS_DATA__;
            if (!data || !data.news) return;
            window.parent.postMessage({
                type: 'a2ui-action',
                detail: {
                    action: {
                        type: 'Action',
                        name: 'show_news',
                        context: [
                            { key: 'symbol', value: { literalString: String(data.symbol || "STOCK") } },
                            { key: 'headline', value: { literalString: String(data.news[index]) } }
                        ]
                    }
                }
            }, '*');
        };

        function render(data) {
            const root = document.getElementById('root');
            if (!data) {
                root.innerHTML = '<div style="padding: 24px; color: #666">Loading Market Data...</div>';
                return;
            }
            window.__STOCKS_DATA__ = data;

            const symbol = data.symbol || "STOCK";
            const company = data.company || "Company Name";
            const price = data.price || "0.00";
            
            const rawChange = data.change || 0;
            const changePercent = data.changePercent || "0.00%";
            
            const isPositive = String(rawChange).indexOf('-') === -1 && Number(rawChange) >= 0;
            const changeStr = isPositive ? `+${rawChange} (+${changePercent.replace('+','')})` : `${rawChange} (${changePercent})`;
            const changeClass = isPositive ? 'change-pill positive' : 'change-pill negative';
            
            const upIcon = '<svg class="change-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
            const downIcon = '<svg class="change-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>';
            const changeIcon = isPositive ? upIcon : downIcon;

            const high = data.high || "--";
            const low = data.low || "--";
            const volume = data.volume || "--";
            const marketCap = data.marketCap || "--";
            
            const newsList = data.news || [];
            
            let newsHtml = '';
            if (newsList.length > 0) {
                const itemsHtml = newsList.slice(0, 2).map((item, index) => {
                    return `<div class="news-item" onclick="handleStockClick(${index})">${item}</div>`;
                }).join('');
                newsHtml = `
                    <div class="news-section">
                        <div class="news-header">Latest Headlines</div>
                        ${itemsHtml}
                    </div>
                `;
            }

            root.innerHTML = `
                <div class="stocks-card">
                    <div class="header">
                        <div>
                            <h2 class="symbol">${symbol}</h2>
                            <p class="company">${company}</p>
                        </div>
                        <div style="display: flex; flex-direction: column; align-items: flex-end">
                            <h1 class="price">$${price}</h1>
                            <div class="${changeClass}">
                                ${changeIcon} <span>${changeStr}</span>
                            </div>
                        </div>
                    </div>

                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-label">Day Range</span>
                            <span class="stat-value">$${low} - $${high}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Volume</span>
                            <span class="stat-value">${volume}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Market Cap</span>
                            <span class="stat-value">${marketCap}</span>
                        </div>
                    </div>
                    
                    ${newsHtml}
                </div>
            `;
        }

        const handler = (event) => {
            if (event.data && event.data.type === 'UPDATE_DATA') {
                render(event.data.data || event.data.widgetData);
            }
        };
        window.addEventListener('message', handler);
        window.parent.postMessage({ type: 'REQUEST_DATA' }, '*');
        
        render(null);
    </script>
</body>
</html>
"""

RESTAURANT_WIDGET_HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 16px; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: transparent; }
        .app-card {
            background: #ffffff;
            border-radius: 20px;
            padding: 24px;
            color: #1f2937;
            box-shadow: 0 12px 30px rgba(0,0,0,0.08);
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 440px;
            margin: 0 auto;
            border: 1px solid #f3f4f6;
        }
        .header { display: flex; flex-direction: column; gap: 8px; }
        .title { font-size: 24px; font-weight: 800; margin: 0; letter-spacing: -0.5px; color: #111827;}
        .subtitle { font-size: 14px; color: #6b7280; margin: 0; }
        
        .search-container {
            position: relative;
            display: flex;
            align-items: center;
        }
        .search-input {
            width: 100%;
            padding: 14px 14px 14px 44px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            font-size: 15px;
            background: #f9fafb;
            transition: all 0.2s;
            outline: none;
            box-sizing: border-box;
        }
        .search-input:focus {
            background: #ffffff;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .search-icon {
            position: absolute;
            left: 14px;
            color: #9ca3af;
            width: 20px;
            height: 20px;
        }

        .category-scroll {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 4px;
            scrollbar-width: none;
        }
        .category-scroll::-webkit-scrollbar { display: none; }
        .pill {
            padding: 6px 14px;
            border-radius: 20px;
            background: #f3f4f6;
            color: #4b5563;
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s;
        }
        .pill:hover { background: #e5e7eb; }
        .pill.active { background: #3b82f6; color: white; }

        .list-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 350px;
            overflow-y: auto;
            padding-right: 4px;
        }
        .list-container::-webkit-scrollbar { width: 6px; }
        .list-container::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 10px; }

        .restaurant-item {
            display: flex;
            gap: 16px;
            padding: 12px;
            border-radius: 16px;
            border: 1px solid #f3f4f6;
            transition: all 0.2s;
            cursor: pointer;
            align-items: center;
        }
        .restaurant-item:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border-color: #e5e7eb;
            transform: translateY(-1px);
        }
        .r-image {
            width: 64px;
            height: 64px;
            border-radius: 12px;
            object-fit: cover;
            background: #f3f4f6;
            flex-shrink: 0;
        }
        .r-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
        .r-name { font-size: 16px; font-weight: 700; color: #111827; margin: 0; }
        .r-meta { font-size: 13px; color: #6b7280; display: flex; align-items: center; gap: 6px; }
        .rating { color: #f59e0b; font-weight: 700; display: flex; align-items: center; gap: 2px;}
        .star { width: 12px; height: 12px; fill: currentColor; }
        
        .no-results {
            padding: 32px 0;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            display: none;
        }
    </style>
</head>
<body>
    <div id="root"></div>
    <script>
        window.__STATE__ = {
            data: null,
            searchQuery: '',
            activeCategory: 'All'
        };

        function setCategory(cat) {
            window.__STATE__.activeCategory = cat;
            renderList();
            renderCategories();
        }

        function handleSearch(e) {
            window.__STATE__.searchQuery = e.target.value.toLowerCase();
            renderList();
        }

        function handleRestaurantClick(id, name) {
            window.parent.postMessage({
                type: 'a2ui-action',
                detail: {
                    action: {
                        type: 'Action',
                        name: 'reserve_table',
                        context: [
                            { key: 'restaurantId', value: { literalString: String(id) } },
                            { key: 'restaurantName', value: { literalString: String(name) } }
                        ]
                    }
                }
            }, '*');
        }

        function extractCategories(list) {
            const cats = new Set(['All']);
            list.forEach(r => { if(r.category) cats.add(r.category); });
            return Array.from(cats);
        }

        function renderCategories() {
            const data = window.__STATE__.data;
            if (!data || !data.restaurants) return;
            
            const categories = extractCategories(data.restaurants);
            const container = document.getElementById('categoryContainer');
            if (categories.length <= 1) {
                container.style.display = 'none';
                return;
            }

            container.innerHTML = categories.map(cat => {
                const isActive = window.__STATE__.activeCategory === cat ? 'active' : '';
                return `<div class="pill ${isActive}" onclick="setCategory('${cat}')">${cat}</div>`;
            }).join('');
        }

        function renderList() {
            const data = window.__STATE__.data;
            if (!data || !data.restaurants) return;
            
            const query = window.__STATE__.searchQuery;
            const cat = window.__STATE__.activeCategory;
            
            const filtered = data.restaurants.filter(r => {
                const matchesSearch = (r.name || '').toLowerCase().includes(query) || 
                                      (r.cuisine || '').toLowerCase().includes(query);
                const matchesCat = cat === 'All' || r.category === cat;
                return matchesSearch && matchesCat;
            });

            const listEl = document.getElementById('listContainer');
            const emptyEl = document.getElementById('emptyState');
            
            if (filtered.length === 0) {
                listEl.style.display = 'none';
                emptyEl.style.display = 'block';
            } else {
                listEl.style.display = 'flex';
                emptyEl.style.display = 'none';
                listEl.innerHTML = filtered.map(r => `
                    <div class="restaurant-item" onclick="handleRestaurantClick('${r.id}', '${r.name}')">
                        <img class="r-image" src="${r.imageUrl || 'http://localhost:10004/static/news.jpg'}" alt="${r.name}">
                        <div class="r-info">
                            <h3 class="r-name">${r.name}</h3>
                            <div class="r-meta">
                                <span class="rating">
                                    <svg class="star" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                                    ${r.rating}
                                </span>
                                <span>•</span>
                                <span>${r.cuisine}</span>
                                <span>•</span>
                                <span>${r.priceRange}</span>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        }

        function render(data) {
            const root = document.getElementById('root');
            if (!data) {
                root.innerHTML = '<div style="padding: 24px; color: #666">Loading Guides...</div>';
                return;
            }
            window.__STATE__.data = data;
            const location = data.location || "Nearby";

            root.innerHTML = `
                <div class="app-card">
                    <div class="header">
                        <h2 class="title">Places to eat in ${location}</h2>
                        <p class="subtitle">Filter and search local spots</p>
                    </div>

                    <div class="search-container">
                        <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path></svg>
                        <input type="text" class="search-input" placeholder="Search by name or cuisine..." onkeyup="handleSearch(event)">
                    </div>

                    <div class="category-scroll" id="categoryContainer"></div>

                    <div class="list-container" id="listContainer"></div>
                    <div class="no-results" id="emptyState">No restaurants found matching your criteria.</div>
                </div>
            `;
            
            renderCategories();
            renderList();
        }

        const handler = (event) => {
            if (event.data && event.data.type === 'UPDATE_DATA') {
                render(event.data.data || event.data.widgetData);
            }
        };
        window.addEventListener('message', handler);
        window.parent.postMessage({ type: 'REQUEST_DATA' }, '*');
        
        render(null);
    </script>
</body>
</html>
"""

WEATHER_WIDGET_SCHEMA = {
  "location": "string (e.g. Sunnyvale, CA)",
  "temperature": "number or string (e.g. 72)",
  "condition": "string (e.g. Sunny, Partly Cloudy, Rain)",
  "icon": "string enum (MUST BE ONE OF: sun, cloud, rain, snow, storm)",
  "humidity": "string (e.g. 60%)",
  "wind": "string (e.g. 10 mph)",
  "forecast": [
    { "day": "string (e.g. Mon)", "high": "string (e.g. 75)", "icon": "string enum" }
  ]
}

STOCKS_WIDGET_SCHEMA = {
  "symbol": "string (e.g. GOOGL)",
  "company": "string (e.g. Alphabet Inc.)",
  "price": "string (e.g. 178.52)",
  "change": "string (e.g. 1.28 or -0.50)",
  "changePercent": "string (e.g. 0.72% or -0.20%)",
  "high": "string (e.g. 180.00)",
  "low": "string (e.g. 175.00)",
  "volume": "string (e.g. 24.5M)",
  "marketCap": "string (e.g. 2.2T)",
  "news": ["string array of 2 recent short headlines related to the company"]
}

RESTAURANT_WIDGET_SCHEMA = {
  "location": "string (e.g. San Francisco, CA)",
  "restaurants": [
    { 
      "id": "string (unique identifier)",
      "name": "string",
      "cuisine": "string (e.g. Italian, Sushi, American)",
      "category": "string (broad grouping e.g. Fine Dining, Casual, Fast Food)",
      "rating": "number (e.g. 4.5)",
      "priceRange": "string (e.g. $$, $$$)",
      "imageUrl": "string absolute URL (must use `http://localhost:10004/static/weather.jpg` if unsure)"
    }
  ]
}

CANNED_WIDGETS = {
    "weather": {
        "htmlContent": WEATHER_WIDGET_HTML,
        "schema": WEATHER_WIDGET_SCHEMA
    },
    "stocks": {
        "htmlContent": STOCKS_WIDGET_HTML,
        "schema": STOCKS_WIDGET_SCHEMA
    },
    "restaurants": {
        "htmlContent": RESTAURANT_WIDGET_HTML,
        "schema": RESTAURANT_WIDGET_SCHEMA
    }
}
