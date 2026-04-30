from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from payouts.models import Merchant, Payout, LedgerEntry
from payouts.services import get_merchant_balance


def home(request):
    merchant = Merchant.objects.first()

    if not merchant:
        return HttpResponse("<h1>Seed data missing. Please run migrations and seed_data.</h1>")

    balance = get_merchant_balance(merchant)
    payouts = Payout.objects.filter(merchant=merchant).order_by("-created_at")[:10]
    ledger_entries = LedgerEntry.objects.filter(merchant=merchant).order_by("-created_at")[:10]

    payout_rows = ""
    for payout in payouts:
        payout_rows += f"""
        <tr>
            <td>{payout.id}</td>
            <td>₹{payout.amount_paise / 100:.2f}</td>
            <td><span class="badge">{payout.status}</span></td>
            <td>{payout.attempts}</td>
        </tr>
        """

    if not payout_rows:
        payout_rows = "<tr><td colspan='4'>No payouts yet. Create one using the button above.</td></tr>"

    ledger_rows = ""
    for entry in ledger_entries:
        ledger_rows += f"""
        <tr>
            <td>{entry.entry_type}</td>
            <td>₹{entry.amount_paise / 100:.2f}</td>
            <td>{entry.description}</td>
            <td>{entry.reference_id}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Playto Payout Engine</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6fb;
                margin: 0;
                padding: 30px;
                color: #111827;
            }}
            .container {{
                max-width: 1100px;
                margin: auto;
            }}
            .header {{
                background: #111827;
                color: white;
                padding: 28px;
                border-radius: 16px;
                margin-bottom: 24px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 16px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.08);
                margin-bottom: 22px;
            }}
            .label {{
                color: #6b7280;
                font-size: 14px;
            }}
            .value {{
                font-size: 30px;
                font-weight: bold;
                margin-top: 8px;
            }}
            button {{
                background: #2563eb;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 10px;
                cursor: pointer;
                font-size: 15px;
                margin-right: 10px;
            }}
            button.secondary {{
                background: #111827;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                margin-bottom: 26px;
            }}
            th, td {{
                padding: 12px;
                border-bottom: 1px solid #e5e7eb;
                text-align: left;
                font-size: 14px;
            }}
            th {{
                background: #eef2ff;
            }}
            .badge {{
                background: #e0f2fe;
                padding: 5px 10px;
                border-radius: 999px;
                font-size: 13px;
            }}
            pre {{
                background: #0f172a;
                color: #e5e7eb;
                padding: 16px;
                border-radius: 12px;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Playto Payout Engine</h1>
                <p>Live backend dashboard showing merchant balance, payouts, ledger entries and idempotency behavior.</p>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="label">Merchant</div>
                    <div class="value">{merchant.name}</div>
                    <p>{merchant.email}</p>
                </div>
                <div class="card">
                    <div class="label">Available Balance</div>
                    <div class="value">₹{balance["available_balance"] / 100:.2f}</div>
                    <p>{balance["available_balance"]} paise</p>
                </div>
                <div class="card">
                    <div class="label">Held Balance</div>
                    <div class="value">₹{balance["held_balance"] / 100:.2f}</div>
                    <p>{balance["held_balance"]} paise</p>
                </div>
            </div>

            <div class="card">
                <h2>Live Demo Actions</h2>
                <p>Create a payout of ₹500 and then retry the same request with the same Idempotency-Key.</p>
                <button onclick="createPayout()">Create Demo Payout</button>
                <button class="secondary" onclick="retrySamePayout()">Retry Same Request</button>
                <pre id="output">Response will appear here...</pre>
            </div>

            <div class="card">
                <h2>Implemented Features</h2>
                <ul>
                    <li>Ledger based accounting in paise</li>
                    <li>Idempotent payout request API</li>
                    <li>Payout hold and release logic</li>
                    <li>Failed payout refund handling</li>
                    <li>Celery compatible payout processing</li>
                    <li>Live APIs for dashboard, payouts and ledger</li>
                </ul>
            </div>

            <h2>Recent Payouts</h2>
            <table>
                <tr>
                    <th>Payout ID</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Attempts</th>
                </tr>
                {payout_rows}
            </table>

            <h2>Recent Ledger Entries</h2>
            <table>
                <tr>
                    <th>Entry Type</th>
                    <th>Amount</th>
                    <th>Description</th>
                    <th>Reference ID</th>
                </tr>
                {ledger_rows}
            </table>
        </div>

        <script>
            let lastKey = localStorage.getItem("last_idempotency_key");
            let lastBody = {{
                amount_paise: 50000,
                bank_account_id: 1
            }};

            function generateUUID() {{
                return crypto.randomUUID();
            }}

            async function createPayout() {{
                lastKey = generateUUID();
                localStorage.setItem("last_idempotency_key", lastKey);

                const response = await fetch("/api/v1/payouts", {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json",
                        "Idempotency-Key": lastKey
                    }},
                    body: JSON.stringify(lastBody)
                }});

                const data = await response.json();
                document.getElementById("output").textContent =
                    "New payout created with key: " + lastKey + "\\n\\n" +
                    JSON.stringify(data, null, 2);

                setTimeout(() => location.reload(), 1500);
            }}

            async function retrySamePayout() {{
                if (!lastKey) {{
                    document.getElementById("output").textContent =
                        "No previous payout key found. Click Create Demo Payout first.";
                    return;
                }}

                const response = await fetch("/api/v1/payouts", {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json",
                        "Idempotency-Key": lastKey
                    }},
                    body: JSON.stringify(lastBody)
                }});

                const data = await response.json();
                document.getElementById("output").textContent =
                    "Retried same request with same key: " + lastKey + "\\n\\n" +
                    JSON.stringify(data, null, 2);
            }}
        </script>
    </body>
    </html>
    """

    return HttpResponse(html)


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/v1/", include("payouts.urls")),
]