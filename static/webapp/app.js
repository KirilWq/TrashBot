// Telegram WebApp initialization
const tg = window.Telegram.WebApp;

// API Base URL
const API_BASE = '/api/webapp';

// Current user data
let userData = {
    id: tg.initDataUnsafe?.user?.id || null,
    username: tg.initDataUnsafe?.user?.username || 'Гравець',
    first_name: tg.initDataUnsafe?.user?.first_name || 'Гравець',
    chat_id: null
};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    // Expand the WebApp
    tg.expand();
    
    // Enable main button color
    tg.MainButton.setParams({
        color: '#667eea',
        text_color: '#ffffff'
    });
    
    // Set theme colors
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#0f0f1a');
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#8b8b9e');
    document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#00d4ff');
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#6c5ce7');
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#1a1a2e');
    
    // Set user info
    document.getElementById('username').textContent = userData.username;
    document.getElementById('userAvatar').textContent = userData.first_name.charAt(0).toUpperCase();
    
    // Setup tabs
    setupTabs();
    
    // Setup chat selector
    loadUserChats();
    
    // Setup MainButton
    tg.MainButton.setText("🍽️ НАГОДУВАТИ ХРЯКА");
    tg.MainButton.onClick(() => {
        feedHryak();
    });
    
    // Load data
    loadUserData();
    
    // Ready
    tg.ready();
    tg.MainButton.show();
}

function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            currentTab = tabId; // Save current tab

            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });

            // Load tab-specific data
            loadTabData(tabId);
        });
    });
}

async function loadUserData() {
    showLoading(true);

    try {
        // Get user data from API
        const url = userData.chat_id 
            ? `${API_BASE}/user?user_id=${userData.id}&chat_id=${userData.chat_id}`
            : `${API_BASE}/user?user_id=${userData.id}`;
        
        console.log('Loading user data from:', url);
        const response = await fetch(url);
        const data = await response.json();
        console.log('User data response:', data);

        if (data.success) {
            const user = data.data;
            console.log('User data:', user);

            // Update header
            document.getElementById('coins').textContent = user.coins || 0;
            document.getElementById('xp').textContent = user.xp || 0;
            document.getElementById('userLevel').textContent = `Рівень ${user.level || 1}`;

            // Update hryak info
            if (user.hryak) {
                console.log('Hryak found:', user.hryak);
                document.getElementById('hryakName').textContent = user.hryak.name;
                document.getElementById('hryakWeight').textContent = `${user.hryak.weight} кг`;
                document.getElementById('maxWeight').textContent = `${user.hryak.max_weight} кг`;
                document.getElementById('feedCount').textContent = user.hryak.feed_count;
                document.getElementById('hryakAvatar').textContent = user.skin?.icon || '🐷';
                document.getElementById('equippedSkin').textContent = user.skin?.display_name || '-';

                // Show feed button if can feed
                const canFeed = user.hryak.can_feed;
                console.log('Can feed:', canFeed);
                if (canFeed) {
                    tg.MainButton.show();
                    tg.MainButton.setParams({
                        color: tg.themeParams.button_color || '#667eea'
                    });
                } else {
                    tg.MainButton.hide();
                }
            } else {
                console.log('No hryak found');
                document.getElementById('hryakName').textContent = 'Немає хряка';
                tg.MainButton.hide();
            }

            // Update stats
            if (user.stats) {
                document.getElementById('duelsStats').textContent = `${user.stats.duels_won || 0}/${user.stats.duels_lost || 0}`;
                document.getElementById('casinoStats').textContent = `${user.stats.casino_wins || 0}/${user.stats.casino_losses || 0}`;
                document.getElementById('trachenStats').textContent = user.trachen_stats?.total_times || 0;
                document.getElementById('tournamentStats').textContent = user.tournament_stats?.tournaments_joined || 0;
                document.getElementById('guildStats').textContent = user.user_guild?.name || '-';
                document.getElementById('bossStats').textContent = user.boss_stats?.bosses_fought || 0;
            }
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        console.error('Error message:', error.message);
        // Don't show alert popup, just log the error
    } finally {
        showLoading(false);
    }
}

function loadTabData(tabId) {
    switch(tabId) {
        case 'shop':
            loadShop();
            loadSkins();
            break;
        case 'inventory':
            loadInventory();
            loadMySkins();
            break;
        case 'leaderboard':
            loadLeaderboard();
            loadGlobalLeaderboard();
            break;
    }
}

async function loadShop() {
    try {
        const response = await fetch(`${API_BASE}/shop`);
        const data = await response.json();
        
        const container = document.getElementById('shopItems');
        container.innerHTML = '';
        
        if (data.success) {
            data.data.forEach(item => {
                const itemEl = document.createElement('div');
                itemEl.className = 'shop-item';
                itemEl.innerHTML = `
                    <div class="icon">${item.name.split(' ')[0]}</div>
                    <div class="name">${item.name}</div>
                    <div class="desc">${item.description}</div>
                    <div class="price">💰 ${item.price}</div>
                    <button class="btn btn-primary" onclick="buyItem('${item.item_id}', ${item.price})">Купити</button>
                `;
                container.appendChild(itemEl);
            });
        }
    } catch (error) {
        console.error('Error loading shop:', error);
    }
}

async function loadSkins() {
    try {
        const response = await fetch(`${API_BASE}/skins`);
        const data = await response.json();
        
        const container = document.getElementById('shopSkins');
        container.innerHTML = '';
        
        if (data.success) {
            data.data.forEach(skin => {
                const skinEl = document.createElement('div');
                skinEl.className = `skin-item rarity-${skin.rarity}`;
                skinEl.innerHTML = `
                    <div class="icon">${skin.icon}</div>
                    <div class="name">${skin.display_name}</div>
                    <div class="desc">${skin.description}</div>
                    <div class="price">💰 ${skin.price}</div>
                    <button class="btn btn-primary" onclick="buySkin('${skin.name}', ${skin.price})">Купити</button>
                `;
                container.appendChild(skinEl);
            });
        }
    } catch (error) {
        console.error('Error loading skins:', error);
    }
}

async function loadInventory() {
    try {
        const response = await fetch(`${API_BASE}/inventory?user_id=${userData.id}`);
        const data = await response.json();
        
        const container = document.getElementById('inventoryItems');
        container.innerHTML = '';
        
        if (data.success && data.data.length > 0) {
            data.data.forEach(item => {
                const itemEl = document.createElement('div');
                itemEl.className = 'inventory-item';
                itemEl.innerHTML = `
                    <div class="item-info">
                        <span class="item-icon">${item.icon || '📦'}</span>
                        <div class="item-details">
                            <span class="item-name">${item.name}</span>
                            <span class="item-quantity">x${item.quantity}</span>
                        </div>
                    </div>
                    <button class="btn btn-primary" style="width: auto; padding: 8px 16px;" onclick="useItem('${item.item_id}')">Використати</button>
                `;
                container.appendChild(itemEl);
            });
        } else {
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--tg-theme-hint-color);">Інвентар порожній</div>';
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

async function loadMySkins() {
    try {
        const chatId = userData.chat_id || -1;
        
        // Load only user's owned skins
        const mySkinsResponse = await fetch(`${API_BASE}/my-skins?user_id=${userData.id}&chat_id=${chatId}`);
        const mySkinsData = await mySkinsResponse.json();

        console.log('My skins:', mySkinsData);

        const container = document.getElementById('mySkins');
        container.innerHTML = '';

        if (mySkinsData.success && mySkinsData.data.length > 0) {
            mySkinsData.data.forEach(skin => {
                const skinEl = document.createElement('div');
                skinEl.className = `my-skin-item rarity-${skin.rarity}`;
                
                const isEquipped = skin.equipped;
                
                skinEl.innerHTML = `
                    <div class="item-info">
                        <span class="item-icon">${skin.icon}</span>
                        <div class="item-details">
                            <span class="item-name">${skin.display_name}</span>
                            <span class="item-quantity">
                                ${isEquipped ? '✅ Одягнуто' : 'У власності'}
                            </span>
                        </div>
                    </div>
                    ${!isEquipped ? 
                        `<button class="btn btn-primary" style="width: auto; padding: 8px 16px;" onclick="equipSkin('${skin.name}')">Одягнути</button>` : 
                        `<button class="btn" disabled style="width: auto; padding: 8px 16px; background: #4caf50; color: white;" disabled>Одягнуто</button>`}
                `;
                container.appendChild(skinEl);
            });
        } else {
            // User has no skins - show default classic skin
            container.innerHTML = `
                <div class="my-skin-item rarity-common">
                    <div class="item-info">
                        <span class="item-icon">🐷</span>
                        <div class="item-details">
                            <span class="item-name">🐷 Класичний</span>
                            <span class="item-quantity">✅ Одягнуто (за замовчуванням)</span>
                        </div>
                    </div>
                    <button class="btn" disabled style="width: auto; padding: 8px 16px; background: #4caf50; color: white;" disabled>Одягнуто</button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading my skins:', error);
    }
}

async function loadLeaderboard() {
    try {
        // Load chat top
        const chatResponse = await fetch(`${API_BASE}/leaderboard/chat`);
        const chatData = await chatResponse.json();

        const chatContainer = document.getElementById('chatTop');
        chatContainer.innerHTML = '';

        if (chatData.success && chatData.data.length > 0) {
            chatData.data.slice(0, 10).forEach((player, index) => {
                const playerEl = document.createElement('div');
                playerEl.className = 'leaderboard-item';
                playerEl.innerHTML = `
                    <span class="rank ${index < 3 ? 'rank-' + (index + 1) : ''}">${index + 1}</span>
                    <div class="leaderboard-info">
                        <span class="leaderboard-avatar">🐷</span>
                        <div class="leaderboard-details">
                            <span class="leaderboard-name">${player.name || 'Невідомо'}</span>
                            <span class="leaderboard-value">${player.weight} кг</span>
                        </div>
                    </div>
                `;
                chatContainer.appendChild(playerEl);
            });
        } else {
            chatContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--tg-theme-hint-color);">Немає гравців</div>';
        }
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

async function loadGlobalLeaderboard() {
    try {
        // Load global top
        const globalResponse = await fetch(`${API_BASE}/leaderboard/global`);
        const globalData = await globalResponse.json();

        const globalContainer = document.getElementById('globalTop');
        globalContainer.innerHTML = '';

        if (globalData.success && globalData.data.length > 0) {
            globalData.data.slice(0, 10).forEach((player, index) => {
                const playerEl = document.createElement('div');
                playerEl.className = 'leaderboard-item';
                playerEl.innerHTML = `
                    <span class="rank ${index < 3 ? 'rank-' + (index + 1) : ''}">${index + 1}</span>
                    <div class="leaderboard-info">
                        <span class="leaderboard-avatar">🐷</span>
                        <div class="leaderboard-details">
                            <span class="leaderboard-name">${player.name || 'Невідомо'}</span>
                            <span class="leaderboard-value">${player.weight} кг</span>
                        </div>
                    </div>
                `;
                globalContainer.appendChild(playerEl);
            });
        } else {
            globalContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--tg-theme-hint-color);">Немає гравців</div>';
        }
    } catch (error) {
        console.error('Error loading global leaderboard:', error);
    }
}

async function feedHryak() {
    tg.showConfirm('Нагодувати хряка?', async (confirm) => {
        if (confirm) {
            showLoading(true);

            try {
                const response = await fetch(`${API_BASE}/feed`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        user_id: userData.id,
                        chat_id: userData.chat_id
                    })
                });

                const data = await response.json();

                if (data.success) {
                    tg.showAlert(`Хряк наївся!\nВага: ${data.data.old_weight} → ${data.data.new_weight} кг (${data.data.change >= 0 ? '+' : ''}${data.data.change})`);
                    loadUserData();
                } else {
                    tg.showAlert(data.message || 'Помилка годування');
                }
            } catch (error) {
                console.error('Error feeding:', error);
                tg.showAlert('Помилка годування');
            } finally {
                showLoading(false);
            }
        }
    });
}

async function buyItem(itemId, price) {
    tg.showConfirm(`Купити предмет за ${price} монет?`, async (confirm) => {
        if (confirm) {
            showLoading(true);

            try {
                const requestBody = {
                    user_id: userData.id,
                    chat_id: userData.chat_id || -1,  // Ensure chat_id is set
                    item_id: itemId
                };
                
                console.log('Buying item:', requestBody);

                const response = await fetch(`${API_BASE}/buy-item`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();
                console.log('Buy item response:', data);

                if (data.success) {
                    tg.showAlert('Куплено!');
                    loadUserData();
                    loadInventory();
                } else {
                    tg.showAlert(data.message || 'Помилка купівлі');
                }
            } catch (error) {
                console.error('Error buying item:', error);
                tg.showAlert('Помилка купівлі');
            } finally {
                showLoading(false);
            }
        }
    });
}

async function buySkin(skinName, price) {
    tg.showConfirm(`Купити скін за ${price} монет?`, async (confirm) => {
        if (confirm) {
            showLoading(true);

            try {
                const requestBody = {
                    user_id: userData.id,
                    chat_id: userData.chat_id || -1,  // Ensure chat_id is set
                    skin_name: skinName
                };
                
                console.log('Buying skin:', requestBody);

                const response = await fetch(`${API_BASE}/buy-skin`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();
                console.log('Buy skin response:', data);

                if (data.success) {
                    tg.showAlert('Куплено!');
                    loadUserData();
                    loadMySkins();
                } else {
                    tg.showAlert(data.message || 'Помилка купівлі');
                }
            } catch (error) {
                console.error('Error buying skin:', error);
                tg.showAlert('Помилка купівлі');
            } finally {
                showLoading(false);
            }
        }
    });
}

async function useItem(itemId) {
    try {
        const response = await fetch(`${API_BASE}/use-item`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userData.id, item_id: itemId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            tg.showAlert('Використано!');
            loadUserData();
            loadInventory();
        } else {
            tg.showAlert(data.message || 'Помилка використання');
        }
    } catch (error) {
        console.error('Error using item:', error);
        tg.showAlert('Помилка використання');
    }
}

async function equipSkin(skinName) {
    try {
        const requestBody = {
            user_id: userData.id,
            chat_id: userData.chat_id || -1,  // Ensure chat_id is set
            skin_name: skinName
        };
        
        console.log('Equipping skin:', requestBody);

        const response = await fetch(`${API_BASE}/equip-skin`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        console.log('Equip skin response:', data);

        if (data.success) {
            tg.showAlert('Одягнуто!');
            loadUserData();
            loadMySkins();
        } else {
            tg.showAlert(data.message || 'Помилка');
        }
    } catch (error) {
        console.error('Error equipping skin:', error);
        tg.showAlert('Помилка');
    }
}

function loadGlobalLeaderboard() {
    // Similar to loadLeaderboard but for global top
}

async function openCommand(command) {
    // Execute command via API
    try {
        const commandPath = command.startsWith('/') ? command.substring(1) : command;
        
        const response = await fetch(`${API_BASE}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userData.id,
                chat_id: userData.chat_id || -1,
                command: commandPath
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            tg.showAlert(`${command}\n\n✅ ${data.message || 'Виконано!'}`);
            loadUserData();
        } else {
            tg.showAlert(`${command}\n\n❌ ${data.message || 'Помилка!'}`);
        }
    } catch (error) {
        console.error('Error executing command:', error);
        tg.showAlert(`${command}\n\n❌ Помилка виконання`);
    }
}

// Bottom nav buttons handlers
function openMenu() {
    openCommand('/menu');
}

function openHelp() {
    openCommand('/help');
}

function openBoss() {
    openCommand('/boss');
}

// Action buttons handlers
function openQuests() {
    openCommand('/quests');
}

function openDaily() {
    openCommand('/daily');
}

function openAchievements() {
    openCommand('/achievements');
}

function openGrow() {
    openCommand('/grow');
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('active');
    } else {
        loading.classList.remove('active');
    }
}

// Handle visibility change
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        loadUserData();
    }
});

// Chat Selector Functions
async function loadUserChats() {
    try {
        const response = await fetch(`${API_BASE}/user-chats?user_id=${userData.id}`);
        const data = await response.json();

        const chatSelect = document.getElementById('chatSelect');
        const chatSelector = document.getElementById('chatSelector');

        if (data.success && data.data.length > 0) {
            chatSelector.style.display = 'block';

            data.data.forEach(chat => {
                const option = document.createElement('option');
                option.value = chat.chat_id;
                option.textContent = `${chat.hryak_name || 'Хряк'} (Чат ${chat.chat_id})`;
                chatSelect.appendChild(option);
            });

            chatSelect.addEventListener('change', (e) => {
                userData.chat_id = e.target.value;
                console.log('✅ Chat changed to:', userData.chat_id);
                // Reload all data for new chat
                loadUserData();
                loadTabData(currentTab || 'profile');
            });

            // Set default chat
            if (data.data.length > 0) {
                userData.chat_id = data.data[0].chat_id;
                chatSelect.value = data.data[0].chat_id;
                console.log('Default chat set to:', userData.chat_id);
            }
        } else {
            console.log('No chats found for user');
        }
    } catch (error) {
        console.error('Error loading chats:', error);
    }
}

// Track current tab
let currentTab = 'profile';
