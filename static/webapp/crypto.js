// TON Connect & Crypto Functions

let tonConnect;
let wallet = null;

function initTonConnect() {
    try {
        tonConnect = new TONConnectSDK.TonConnect({
            manifestUrl: 'https://trashbot-n0nd.onrender.com/tonconnect-manifest.json'
        });
        
        tonConnect.onStatusChange(walletInfo => {
            wallet = walletInfo;
            if (wallet) {
                const walletInput = document.getElementById('walletAddress');
                if (walletInput) {
                    walletInput.value = wallet.account.address;
                }
                console.log('TON Wallet connected:', wallet.account.address);
            } else {
                wallet = null;
                console.log('TON Wallet disconnected');
            }
        });
    } catch (error) {
        console.error('TON Connect init error:', error);
    }
}

async function connectTonWallet() {
    if (!tonConnect) {
        initTonConnect();
    }
    
    try {
        await tonConnect.openModal();
    } catch (error) {
        console.error('Connect wallet error:', error);
        if (typeof tg !== 'undefined') {
            tg.showAlert('Помилка підключення гаманця');
        }
    }
}

async function loadCryptoData() {
    try {
        const response = await fetch(`${API_BASE}/crypto-info?user_id=${userData.id}&chat_id=${userData.chat_id || -1}`);
        const data = await response.json();
        
        console.log('Crypto data:', data);
        
        if (data.success) {
            const gameCoinsEl = document.getElementById('gameCoins');
            const cryptoCoinsEl = document.getElementById('cryptoCoins');
            const totalConvertedEl = document.getElementById('totalConverted');
            
            if (gameCoinsEl) gameCoinsEl.textContent = data.data.game_coins.toLocaleString();
            if (cryptoCoinsEl) cryptoCoinsEl.textContent = `${data.data.crypto_coins.toLocaleString()} CRYPTO`;
            if (totalConvertedEl) totalConvertedEl.textContent = `${data.data.total_converted.toLocaleString()} монет`;
            
            const convertInput = document.getElementById('convertAmount');
            if (convertInput) {
                convertInput.addEventListener('input', updateCryptoPreview);
            }
        }
        
        // Load transaction history
        loadTransactionHistory();
    } catch (error) {
        console.error('Error loading crypto data:', error);
    }
}

async function loadTransactionHistory() {
    try {
        const response = await fetch(`${API_BASE}/transactions?user_id=${userData.id}&chat_id=${userData.chat_id || -1}&limit=10`);
        const data = await response.json();
        
        const transactionList = document.getElementById('transactionList');
        
        if (!data.success || !data.data || data.data.length === 0) {
            if (transactionList) {
                transactionList.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--tg-theme-hint-color);">Немає транзакцій</div>';
            }
            return;
        }
        
        if (transactionList) {
            transactionList.innerHTML = data.data.map(tx => {
                const isConvert = tx.transaction_type === 'convert';
                const amountClass = isConvert ? 'positive' : 'negative';
                const typeText = isConvert ? '🔄 Конвертація' : '💸 Виведення';
                const statusClass = tx.status;
                const statusText = tx.status === 'pending' ? 'Очікує' : (tx.status === 'completed' ? 'Виконано' : 'Скасовано');
                const date = new Date(tx.created_at * 1000).toLocaleDateString();
                
                return `
                    <div class="transaction-item">
                        <div class="transaction-info">
                            <div class="transaction-type ${tx.transaction_type}">${typeText}</div>
                            <div class="transaction-details">${date}</div>
                            <span class="transaction-status ${statusClass}">${statusText}</span>
                        </div>
                        <div class="transaction-amount ${amountClass}">
                            ${isConvert ? '+' : '-'}{(tx.amount / 1000).toFixed(2)} CRYPTO
                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

function updateCryptoPreview() {
    const amount = parseInt(document.getElementById('convertAmount').value) || 0;
    const preview = amount / 1000;
    const previewEl = document.getElementById('cryptoPreview');
    if (previewEl) {
        previewEl.textContent = preview.toFixed(2);
    }
}

async function convertCoins() {
    const amount = parseInt(document.getElementById('convertAmount').value);
    
    if (!amount || amount < 10000) {
        if (typeof tg !== 'undefined') {
            tg.showAlert('Мінімум для конвертації: 10,000 монет');
        } else {
            alert('Мінімум для конвертації: 10,000 монет');
        }
        return;
    }
    
    const cryptoAmount = (amount / 1000).toFixed(2);
    
    if (typeof tg !== 'undefined') {
        tg.showConfirm(`Конвертувати ${amount.toLocaleString()} монет в ${cryptoAmount} CRYPTO?`, async (confirm) => {
            if (confirm) {
                await processConversion(amount, cryptoAmount);
            }
        });
    } else {
        if (confirm(`Конвертувати ${amount.toLocaleString()} монет в ${cryptoAmount} CRYPTO?`)) {
            await processConversion(amount, cryptoAmount);
        }
    }
}

async function processConversion(amount, cryptoAmount) {
    if (typeof showLoading !== 'undefined') showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/convert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userData.id,
                chat_id: userData.chat_id || -1,
                amount: amount
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const message = `✅ Конвертація успішна!\n\nСписано: ${data.data.game_coins_deducted.toLocaleString()} монет\nОтримано: ${data.data.crypto_received.toFixed(2)} CRYPTO`;
            if (typeof tg !== 'undefined') {
                tg.showAlert(message);
            } else {
                alert(message);
            }
            loadCryptoData();
            if (typeof loadUserData !== 'undefined') loadUserData();
        } else {
            const errorMsg = `❌ ${data.message}`;
            if (typeof tg !== 'undefined') {
                tg.showAlert(errorMsg);
            } else {
                alert(errorMsg);
            }
        }
    } catch (error) {
        console.error('Convert error:', error);
        if (typeof tg !== 'undefined') {
            tg.showAlert('Помилка конвертації');
        } else {
            alert('Помилка конвертації');
        }
    } finally {
        if (typeof showLoading !== 'undefined') showLoading(false);
    }
}

async function withdrawCrypto() {
    const amount = parseInt(document.getElementById('withdrawAmount').value);
    const walletAddress = document.getElementById('walletAddress').value.trim();
    
    if (!amount || amount < 10) {
        if (typeof tg !== 'undefined') {
            tg.showAlert('Мінімум для виведення: 10 CRYPTO');
        } else {
            alert('Мінімум для виведення: 10 CRYPTO');
        }
        return;
    }
    
    if (!walletAddress || !walletAddress.startsWith('kQ')) {
        if (typeof tg !== 'undefined') {
            tg.showAlert('Будь ласка, введіть правильну адресу TON гаманця (починається з kQ)');
        } else {
            alert('Будь ласка, введіть правильну адресу TON гаманця (починається з kQ)');
        }
        return;
    }
    
    if (typeof tg !== 'undefined') {
        tg.showConfirm(`Вивести ${amount} CRYPTO на гаманець?\n\n${walletAddress}`, async (confirm) => {
            if (confirm) {
                await processWithdrawal(amount, walletAddress);
            }
        });
    } else {
        if (confirm(`Вивести ${amount} CRYPTO на гаманець?\n\n${walletAddress}`)) {
            await processWithdrawal(amount, walletAddress);
        }
    }
}

async function processWithdrawal(amount, walletAddress) {
    if (typeof showLoading !== 'undefined') showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/withdraw`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userData.id,
                chat_id: userData.chat_id || -1,
                amount: amount,
                wallet_address: walletAddress
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const message = `✅ Виведення створено!\n\nСума: ${amount} CRYPTO\nГаманець: ${walletAddress}\n\nСтатус: Очікує підтвердження`;
            if (typeof tg !== 'undefined') {
                tg.showAlert(message);
            } else {
                alert(message);
            }
            loadCryptoData();
        } else {
            const errorMsg = `❌ ${data.message}`;
            if (typeof tg !== 'undefined') {
                tg.showAlert(errorMsg);
            } else {
                alert(errorMsg);
            }
        }
    } catch (error) {
        console.error('Withdraw error:', error);
        if (typeof tg !== 'undefined') {
            tg.showAlert('Помилка виведення');
        } else {
            alert('Помилка виведення');
        }
    } finally {
        if (typeof showLoading !== 'undefined') showLoading(false);
    }
}

// Initialize TON Connect when DOM is ready
if (typeof TONConnectSDK !== 'undefined') {
    initTonConnect();
}
