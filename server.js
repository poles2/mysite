/**
 * Secure Lightning Payout Backend Server (Node.js / Express)
 * Serves index.html Dashboard + Speed API Integration
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const https = require('https');
const path = require('path');

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Serve static files (including index.html)
app.use(express.static(__dirname));

const SPEED_SECRET_KEY = "sk_live_l3o6dqxz6yJrb75Gl7ef0t0ufhhmuOV265zz6eZJST6GnqjK";
const SPEED_PUBLIC_KEY = "pk_live_l3o6d77z6yJrbuCGl7ef0s9nsuR5kWPyvNhOteD7O58hieSR";

// Serve index.html Dashboard at Root "/"
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Speed API Withdrawal Endpoint
app.post('/api/withdraw', (req, res) => {
    const { lightningAddress, amountSats } = req.body;

    if (!lightningAddress || !amountSats) {
        return res.status(400).json({ success: false, error: "Missing lightningAddress or amountSats" });
    }

    console.log(`\n=================================================`);
    console.log(`[PAYOUT REQUEST] Amount: ${amountSats} Sats -> Address: ${lightningAddress}`);

    const authHeader = 'Basic ' + Buffer.from(SPEED_SECRET_KEY + ':').toString('base64');
    const payload = JSON.stringify({
        destination: lightningAddress,
        amount: Number(amountSats),
        currency: "SATS"
    });

    const options = {
        hostname: 'api.tryspeed.com',
        port: 443,
        path: '/v1/payout',
        method: 'POST',
        headers: {
            'Authorization': authHeader,
            'X-Public-Key': SPEED_PUBLIC_KEY,
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload)
        }
    };

    const speedReq = https.request(options, (speedRes) => {
        let responseData = '';

        speedRes.on('data', (chunk) => {
            responseData += chunk;
        });

        speedRes.on('end', () => {
            console.log(`[SPEED API STATUS] ${speedRes.statusCode}`);
            console.log(`[SPEED API RESPONSE] ${responseData}`);

                        try {
                const response = await fetch('/api/v1/claim', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        payout_destination: destination,
                        claimed_sats: totalMined,
                        auto_payout: false
                    })
                });

                if (!response.ok) throw new Error(`Błąd serwera: ${response.status}`);

                const data = await response.json();
                
                document.getElementById('statusText').innerText = data.status;
                document.getElementById('balanceText').innerText = `Wypłacono: ${totalMined} sats`;
                document.getElementById('txidText').innerText = data.txid || "Brak TXID"; // <-- TUTAJ WPISUJEMY TXID
                document.getElementById('messageText').innerText = `${data.message} na adres ${destination}`;
                
                resultBox.classList.remove('hidden');
                showToast(`Wypłacono pomyślnie ${totalMined} sats!`);

                jsMined = 0;
                cloudMined = 0;
                document.getElementById('jsMined').innerText = '0';
                document.getElementById('cloudMined').innerText = '0';

            } catch (error) { ... }
                    const data = await response.json();
                    
                    showToast(`Auto-wypłata ${totalMined} sats zakończona!`);
                    
                    // Pokazujemy wynik również w okienku dla auto-payoutu
                    document.getElementById('statusText').innerText = data.status;
                    document.getElementById('balanceText').innerText = `Auto-wypłata: ${totalMined} sats`;
                    document.getElementById('txidText').innerText = data.txid || "Brak TXID"; // <-- TUTAJ RÓWNIEŻ
                    document.getElementById('messageText').innerText = `Przesłano automatycznie na ${destination}`;
                    document.getElementById('resultBox').classList.remove('hidden');

                    jsMined = 0;
                    cloudMined = 0;
                    document.getElementById('jsMined').innerText = '0';
                    document.getElementById('cloudMined').innerText = '0';
        function copyTxidToClipboard() {
            const txidElement = document.getElementById('txidText');
            const txidText = txidElement.innerText;

            if (!txidText || txidText === '-') {
                showToast('Brak TXID do skopiowania!');
                return;
            }

            navigator.clipboard.writeText(txidText).then(() => {
                showToast('Skopiowano TXID do schowka!');
                
                // Opcjonalna zmiana tekstu przycisku na chwilę
                const copyBtn = document.getElementById('copyTxidBtn');
                const originalText = copyBtn.innerText;
                copyBtn.innerText = 'Skopiowano!';
                copyBtn.style.backgroundColor = '#27ae60';
                copyBtn.style.color = 'white';

                setTimeout(() => {
                    copyBtn.innerText = originalText;
                    copyBtn.style.backgroundColor = '#e2e8f0';
                    copyBtn.style.color = '#333';
                }, 2000);

            }).catch(err => {
                console.error('Nie udało się skopiować: ', err);
                alert('Nie udało się skopiować TXID do schowka.');
            });
        }


    speedReq.on('error', (err) => {
        console.error('[SPEED API ERROR]', err.message);
        res.status(500).json({ success: false, error: err.message });
    });

    speedReq.write(payload);
    speedReq.end();
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`=================================================`);
    console.log(`🚀 Speed Payout Server & Web Dashboard running on port ${PORT}`);
    console.log(`🌐 Open http://localhost:${PORT} in your browser to access UI!`);
    console.log(`=================================================`);
});
