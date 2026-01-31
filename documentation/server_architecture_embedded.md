# Bensoft.be Server Architecture

<details open>
<summary>Click to view the HTML visualization</summary>

<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bensoft.be Server Architectuur</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }

        .subtitle {
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 40px;
            font-size: 1.1em;
        }

        .architecture {
            display: flex;
            flex-direction: column;
            gap: 30px;
            margin-top: 40px;
        }

        .layer {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            border-left: 5px solid #3498db;
        }

        .layer-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .layer-title .icon {
            font-size: 1.5em;
        }

        .boxes {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }

        .box {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
        }

        .box:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
            border-color: #3498db;
        }

        .box-title {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .box-content {
            color: #555;
            font-size: 0.95em;
            line-height: 1.6;
        }

        .box-detail {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.85em;
            color: #7f8c8d;
        }

        .arrow {
            text-align: center;
            font-size: 2em;
            color: #3498db;
            margin: 10px 0;
        }

        .flow-line {
            display: flex;
            align-items: center;
            gap: 15px;
            margin: 15px 0;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 8px;
        }

        .flow-arrow {
            color: #3498db;
            font-size: 1.5em;
            font-weight: bold;
        }

        .flow-text {
            flex: 1;
            color: #2c3e50;
        }

        .highlight {
            background: #fff3cd;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        .success {
            color: #27ae60;
            font-weight: bold;
        }

        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
        }

        .info-box h3 {
            color: #1976d2;
            margin-bottom: 10px;
        }

        .info-box ul {
            margin-left: 20px;
            color: #555;
        }

        .info-box li {
            margin: 5px 0;
        }

        .specs {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .spec-item {
            background: #f0f0f0;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 0.9em;
        }

        .spec-label {
            font-weight: bold;
            color: #2c3e50;
        }

        .spec-value {
            color: #555;
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }

            h1 {
                font-size: 1.8em;
            }

            .boxes {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 Bensoft.be Server Architectuur</h1>
        <p class="subtitle">Nginx Reverse Proxy met SSL/TLS en Docker Containers</p>

        <div class="architecture">

            <!-- Layer 1: Internet -->
            <div class="layer" style="border-left-color: #e74c3c;">
                <div class="layer-title">
                    <span class="icon">🌍</span>
                    <span>Layer 1: Internet & DNS</span>
                </div>
                <div class="boxes">
                    <div class="box">
                        <div class="box-title">🔗 Publiek Toegangspunt</div>
                        <div class="box-content">
                            Publiek IP: <span class="highlight">78.21.255.210</span>
                            <div class="box-detail">
                                <strong>DNS Records:</strong><br>
                                • bensoft.be → 78.21.255.210<br>
                                • www.bensoft.be → 78.21.255.210<br>
                                • api.bensoft.be → 78.21.255.210
                            </div>
                        </div>
                    </div>
                    <div class="box">
                        <div class="box-title">👥 Gebruikers</div>
                        <div class="box-content">
                            Toegang via:<br>
                            • <span class="highlight">https://bensoft.be</span><br>
                            • <span class="highlight">https://www.bensoft.be</span><br>
                            • <span class="highlight">https://api.bensoft.be</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="arrow">⬇️</div>

            <!-- Layer 2: Router -->
            <div class="layer" style="border-left-color: #f39c12;">
                <div class="layer-title">
                    <span class="icon">🔀</span>
                    <span>Layer 2: Router & Firewall</span>
                </div>
                <div class="boxes">
                    <div class="box">
                        <div class="box-title">📡 Port Forwarding</div>
                        <div class="box-content">
                            <strong>Router regels:</strong>
                            <div class="specs">
                                <div class="spec-item">
                                    <div class="spec-label">Poort 80 (HTTP)</div>
                                    <div class="spec-value">→ 192.168.0.30:80</div>
                                </div>
                                <div class="spec-item">
                                    <div class="spec-label">Poort 443 (HTTPS)</div>
                                    <div class="spec-value">→ 192.168.0.30:443</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="box">
                        <div class="box-title">🛡️ Netwerk</div>
                        <div class="box-content">
                            Van internet (78.21.255.210)<br>
                            naar intern netwerk (192.168.0.x)
                            <div class="box-detail">
                                Alleen poort 80 en 443 toegestaan
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="arrow">⬇️</div>

            <!-- Layer 3: Ubuntu Server -->
            <div class="layer" style="border-left-color: #9b59b6;">
                <div class="layer-title">
                    <span class="icon">🖥️</span>
                    <span>Layer 3: Ubuntu Server 25.10</span>
                </div>
                <div class="boxes">
                    <div class="box">
                        <div class="box-title">💻 Server Details</div>
                        <div class="box-content">
                            <strong>IP:</strong> <span class="highlight">192.168.0.30</span><br>
                            <strong>OS:</strong> Ubuntu Server 25.10<br>
                            <strong>Services:</strong> Nginx, Docker, UFW
                        </div>
                    </div>
                    <div class="box">
                        <div class="box-title">🔥 UFW Firewall</div>
                        <div class="box-content">
                            <strong>Toegestane poorten:</strong><br>
                            • Nginx Full (80, 443)<br>
                            • OpenSSH (22)<br>
                            • Verkeer van 192.168.0.0/24
                        </div>
                    </div>
                </div>
            </div>

            <div class="arrow">⬇️</div>

            <!-- Layer 4: Nginx -->
            <div class="layer" style="border-left-color: #27ae60;">
                <div class="layer-title">
                    <span class="icon">🔄</span>
                    <span>Layer 4: Nginx Reverse Proxy</span>
                </div>
                <div class="boxes">
                    <div class="box">
                        <div class="box-title">🔐 SSL/TLS Terminatie</div>
                        <div class="box-content">
                            <strong>Let's Encrypt Certificaten</strong><br>
                            • Automatische HTTPS<br>
                            • HTTP → HTTPS redirect<br>
                            • TLS 1.2 & 1.3<br>
                            • Auto-renewal elke 60 dagen
                            <div class="box-detail">
                                Certificaten: /etc/letsencrypt/live/bensoft.be/
                            </div>
                        </div>
                    </div>
                    <div class="box">
                        <div class="box-title">🎯 Routing Logic</div>
                        <div class="box-content">
                            <strong>Domein → Backend:</strong><br>
                            • bensoft.be → localhost:8500<br>
                            • www.bensoft.be → localhost:8500<br>
                            • api.bensoft.be → localhost:8550
                            <div class="box-detail">
                                Config: /etc/nginx/sites-available/bensoft.be
                            </div>
                        </div>
                    </div>
                    <div class="box">
                        <div class="box-title">📝 Proxy Headers</div>
                        <div class="box-content">
                            Headers doorgegeven aan backend:<br>
                            • X-Real-IP<br>
                            • X-Forwarded-For<br>
                            • X-Forwarded-Proto<br>
                            • Host<br>
                            • WebSocket support (Upgrade)
                        </div>
                    </div>
                </div>
            </div>

            <div class="arrow">⬇️</div>

            <!-- Layer 5: Docker -->
            <div class="layer" style="border-left-color: #3498db;">
                <div class="layer-title">
                    <span class="icon">🐳</span>
                    <span>Layer 5: Docker Containers</span>
                </div>
                <div class="boxes">
                    <div class="box">
                        <div class="box-title">📦 Container: Hoofdapplicatie</div>
                        <div class="box-content">
                            <strong>Poort:</strong> <span class="highlight">localhost:8500</span><br>
                            <strong>Server:</strong> uvicorn<br>
                            <strong>Toegankelijk via:</strong><br>
                            • https://bensoft.be<br>
                            • https://www.bensoft.be
                            <div class="box-detail">
                                ⚠️ Alleen bereikbaar vanaf localhost
                            </div>
                        </div>
                    </div>
                    <div class="box">
                        <div class="box-title">📦 Container: API</div>
                        <div class="box-content">
                            <strong>Poort:</strong> <span class="highlight">localhost:8550</span><br>
                            <strong>Toegankelijk via:</strong><br>
                            • https://api.bensoft.be
                            <div class="box-detail">
                                ⚠️ Alleen bereikbaar vanaf localhost
                            </div>
                        </div>
                    </div>
                    <div class="box">
                        <div class="box-title">📦 Container: Mail (Optioneel)</div>
                        <div class="box-content">
                            <strong>Poort:</strong> <span class="highlight">localhost:8025</span><br>
                            <strong>Status:</strong> Klaar voor gebruik<br>
                            <div class="box-detail">
                                Kan toegevoegd worden met mail.bensoft.be
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Request Flow -->
        <div class="info-box" style="margin-top: 50px;">
            <h3>🔄 Request Flow: https://bensoft.be naar Docker Container</h3>

            <div class="flow-line">
                <span class="flow-arrow">1️⃣</span>
                <div class="flow-text">
                    <strong>Gebruiker</strong> opent <span class="highlight">https://bensoft.be</span> in browser
                </div>
            </div>

            <div class="flow-line">
                <span class="flow-arrow">2️⃣</span>
                <div class="flow-text">
                    <strong>DNS</strong> resolveert bensoft.be naar <span class="highlight">78.21.255.210</span>
                </div>
            </div>

            <div class="flow-line">
                <span class="flow-arrow">3️⃣</span>
                <div class="flow-text">
                    <strong>Router</strong> ontvangt request op poort 443 en forwardt naar <span class="highlight">192.168.0.30:443</span>
                </div>
            </div>

            <div class="flow-line">
                <span class="flow-arrow">4️⃣</span>
                <div class="flow-text">
                    <strong>UFW Firewall</strong> controleert en staat verkeer toe (Nginx Full regel)
                </div>
            </div>

            <div class="flow-line">
                <span class="flow-arrow">5️⃣</span>
                <div class="flow-text">
                    <strong>Nginx</strong> ontvangt HTTPS request, verifieert SSL certificaat en decrypts
                </div>
            </div>

            <div class="flow-line">
                <span class="flow-arrow">6️⃣</span>
                <div class="flow-text">
                    <strong>Nginx</strong> checkt server_name (bensoft.be) en route naar <span class="highlight">http://localhost:8500</span>
                </div>
            </div>

            <div class="flow-line">
                <span class="flow-arrow">7️⃣</span>
                <div class="flow-text">
                    <strong>Docker Container</strong> (uvicorn) ontvangt request op poort 8500 en verwerkt
                </div>
            </div>

            <div class="flow-line">
                <span class="flow-arrow">8️⃣</span>
                <div class="flow-text">
                    <strong>Response</strong> gaat terug via Nginx (encryptie) → Router → Internet → <span class="success">Gebruiker ✓</span>
                </div>
            </div>
        </div>

        <!-- Security Features -->
        <div class="info-box" style="background: #fff3cd; border-left-color: #f39c12;">
            <h3>🔒 Beveiligingslagen</h3>
            <ul>
                <li><strong>SSL/TLS Encryptie:</strong> Alle verkeer tussen gebruiker en server is versleuteld (HTTPS)</li>
                <li><strong>Automatische HTTP → HTTPS redirect:</strong> Alle HTTP requests worden omgeleid naar HTTPS</li>
                <li><strong>Firewall (UFW):</strong> Alleen poort 80, 443 en SSH toegestaan van buitenaf</li>
                <li><strong>Docker Isolatie:</strong> Containers alleen bereikbaar via localhost, niet direct van internet</li>
                <li><strong>Nginx als Gateway:</strong> Alle requests gaan door één beveiligde toegangspunt</li>
                <li><strong>Let's Encrypt:</strong> Gratis, automatisch vernieuwende certificaten</li>
            </ul>
        </div>

        <!-- Technical Specs -->
        <div class="info-box" style="background: #e8f5e9; border-left-color: #4caf50;">
            <h3>⚙️ Technische Specificaties</h3>
            <div class="specs" style="margin-top: 15px;">
                <div class="spec-item">
                    <div class="spec-label">OS</div>
                    <div class="spec-value">Ubuntu Server 25.10</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Web Server</div>
                    <div class="spec-value">Nginx 1.24.0</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">SSL Provider</div>
                    <div class="spec-value">Let's Encrypt (Certbot)</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Container Platform</div>
                    <div class="spec-value">Docker</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Firewall</div>
                    <div class="spec-value">UFW (Uncomplicated Firewall)</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">TLS Versies</div>
                    <div class="spec-value">TLS 1.2, TLS 1.3</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">HTTP Versies</div>
                    <div class="spec-value">HTTP/1.1, HTTP/2</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Cert Renewal</div>
                    <div class="spec-value">Automatisch elke 60 dagen</div>
                </div>
            </div>
        </div>

        <!-- File Locations -->
        <div class="info-box">
            <h3>📁 Belangrijke Bestanden & Locaties</h3>
            <ul>
                <li><strong>Nginx Config:</strong> <code>/etc/nginx/sites-available/bensoft.be</code></li>
                <li><strong>SSL Certificaten:</strong> <code>/etc/letsencrypt/live/bensoft.be/</code></li>
                <li><strong>Nginx Logs:</strong> <code>/var/log/nginx/access.log</code> & <code>error.log</code></li>
                <li><strong>Certbot Logs:</strong> <code>/var/log/letsencrypt/letsencrypt.log</code></li>
                <li><strong>Firewall Rules:</strong> <code>sudo ufw status</code></li>
            </ul>
        </div>

    </div>
</body>
</html>

</details>
