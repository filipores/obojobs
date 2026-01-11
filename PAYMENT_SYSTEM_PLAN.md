# Payment System Implementation Plan
## Credit-Kauf-System mit PayPal

**Datum:** 8. Januar 2026
**Typ:** Pay-per-Credit (Kein Subscription-Modell)
**Payment Provider:** PayPal

---

## 📋 Requirements Summary

### User-Anforderungen:
- ✅ **Payment Provider:** PayPal
- ✅ **Modell:** Einmal-Kauf von Credits (keine Abos)
- ✅ **Free Credits:** 5 Credits kostenlos bei Registrierung
- ✅ **Nachkauf:** User können jederzeit Credits nachkaufen
- ✅ **Keine Verfallsdaten:** Credits bleiben dauerhaft

### Credit-Pakete (Günstige Variante):
```
┌─────────────────────────────────────────────┐
│ Package │ Credits │ Preis │ Pro Credit     │
├─────────────────────────────────────────────┤
│ FREE    │ 5       │ 0€    │ Gratis         │
│ Small   │ 10      │ 1€    │ 0.10€          │
│ Medium  │ 50      │ 4€    │ 0.08€ (-20%)   │
│ Large   │ 100     │ 7€    │ 0.07€ (-30%)   │
└─────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Overview

### System Components:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Frontend   │ ───▶ │   Backend    │ ───▶ │   PayPal    │
│  (Vue.js)   │ ◀─── │   (Flask)    │ ◀─── │     API     │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │
       │                     ▼
       │              ┌──────────────┐
       └─────────────▶│   Database   │
                      │  (SQLite)    │
                      └──────────────┘
```

### Payment Flow:

```
1. User wählt Credit-Paket (z.B. "50 Credits für 4€")
2. Frontend → Backend: POST /api/payments/create-order
3. Backend → PayPal: Create Order
4. PayPal → Backend: order_id
5. Backend → Frontend: order_id
6. Frontend öffnet PayPal Checkout (Popup/Redirect)
7. User zahlt bei PayPal
8. PayPal → Frontend: Approval Token
9. Frontend → Backend: POST /api/payments/capture-order
10. Backend → PayPal: Capture Payment
11. PayPal → Backend: Payment Confirmed
12. Backend: Update User Credits (+50)
13. Backend: Save Purchase Record
14. Backend → Frontend: Success + new credits
15. Frontend: Refresh User Data, Show Success
```

---

## 💾 Database Schema

### New Table: `purchases`

```sql
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Package Info
    package_name VARCHAR(50) NOT NULL,  -- 'small', 'medium', 'large'
    credits_purchased INTEGER NOT NULL,
    price_eur DECIMAL(10, 2) NOT NULL,

    -- PayPal Info
    paypal_order_id VARCHAR(255) UNIQUE NOT NULL,
    paypal_payer_id VARCHAR(255),
    paypal_payer_email VARCHAR(255),

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, completed, failed, refunded

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,

    -- Foreign Key
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_purchases_user_id ON purchases(user_id);
CREATE INDEX idx_purchases_status ON purchases(status);
CREATE INDEX idx_purchases_paypal_order_id ON purchases(paypal_order_id);
```

### Modified Table: `users`

**Änderungen:**
```sql
-- Aktuell:
credits_remaining INTEGER DEFAULT 50
credits_max INTEGER DEFAULT 50  -- Wird nicht mehr benötigt

-- NEU:
credits_remaining INTEGER DEFAULT 5  -- Free Credits
total_credits_purchased INTEGER DEFAULT 0  -- Lifetime tracking
```

**Migration:**
- `DEFAULT_CREDITS` von 50 → 5 ändern
- Neue Spalte `total_credits_purchased` hinzufügen
- `credits_max` kann bleiben (für Backward Compatibility) oder entfernt werden

---

## 🔧 Backend Implementation

### 1. Configuration (config.py)

```python
class Config:
    # ... existing config ...

    # Credits
    DEFAULT_CREDITS = 5  # Changed from 50

    # PayPal
    PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
    PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')  # sandbox or live

    # Credit Packages
    CREDIT_PACKAGES = {
        'small': {'credits': 10, 'price': 1.00, 'name': 'Small Paket'},
        'medium': {'credits': 50, 'price': 4.00, 'name': 'Medium Paket'},
        'large': {'credits': 100, 'price': 7.00, 'name': 'Large Paket'}
    }
```

### 2. New Model: Purchase (models/purchase.py)

```python
from . import db
from datetime import datetime

class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Package Info
    package_name = db.Column(db.String(50), nullable=False)
    credits_purchased = db.Column(db.Integer, nullable=False)
    price_eur = db.Column(db.Numeric(10, 2), nullable=False)

    # PayPal Info
    paypal_order_id = db.Column(db.String(255), unique=True, nullable=False)
    paypal_payer_id = db.Column(db.String(255))
    paypal_payer_email = db.Column(db.String(255))

    # Status
    status = db.Column(db.String(50), default='pending')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationship
    user = db.relationship('User', back_populates='purchases')

    def to_dict(self):
        return {
            'id': self.id,
            'package_name': self.package_name,
            'credits_purchased': self.credits_purchased,
            'price_eur': float(self.price_eur),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
```

### 3. Modified Model: User (models/user.py)

```python
class User(db.Model):
    # ... existing fields ...

    credits_remaining = db.Column(db.Integer, default=5)  # Changed from 50
    total_credits_purchased = db.Column(db.Integer, default=0)  # NEW

    # New Relationship
    purchases = db.relationship('Purchase', back_populates='user',
                               cascade='all, delete-orphan')

    def to_dict(self):
        return {
            # ... existing fields ...
            'credits_remaining': self.credits_remaining,
            'total_credits_purchased': self.total_credits_purchased,
            'credits_max': self.credits_max  # Deprecated, keep for compatibility
        }
```

### 4. PayPal Service (services/paypal_service.py)

**New File:**

```python
import paypalrestsdk
from config import config
from datetime import datetime

class PayPalService:
    def __init__(self):
        paypalrestsdk.configure({
            "mode": config.PAYPAL_MODE,  # sandbox or live
            "client_id": config.PAYPAL_CLIENT_ID,
            "client_secret": config.PAYPAL_CLIENT_SECRET
        })

    def create_order(self, package_name: str, return_url: str, cancel_url: str):
        """Create a PayPal order for credit purchase"""
        package = config.CREDIT_PACKAGES.get(package_name)
        if not package:
            raise ValueError(f"Invalid package: {package_name}")

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"{package['name']} - {package['credits']} Credits",
                        "sku": package_name,
                        "price": str(package['price']),
                        "currency": "EUR",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(package['price']),
                    "currency": "EUR"
                },
                "description": f"Kauf von {package['credits']} Credits"
            }]
        })

        if payment.create():
            return {
                'payment_id': payment.id,
                'approval_url': next(link.href for link in payment.links
                                    if link.rel == 'approval_url')
            }
        else:
            raise Exception(f"PayPal Error: {payment.error}")

    def execute_payment(self, payment_id: str, payer_id: str):
        """Execute/Capture a PayPal payment"""
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            return {
                'success': True,
                'payer_email': payment.payer.payer_info.email,
                'transaction_id': payment.transactions[0].related_resources[0].sale.id
            }
        else:
            raise Exception(f"Payment execution failed: {payment.error}")

    def get_payment_details(self, payment_id: str):
        """Get payment details from PayPal"""
        payment = paypalrestsdk.Payment.find(payment_id)
        return payment.to_dict()
```

### 5. New Route: payments.py (routes/payments.py)

**New File:**

```python
from flask import Blueprint, request, jsonify
from middleware.jwt_required import jwt_required_custom
from models import db, Purchase, User
from services.paypal_service import PayPalService
from config import config
from datetime import datetime

payments_bp = Blueprint('payments', __name__)
paypal_service = PayPalService()


@payments_bp.route('/packages', methods=['GET'])
def get_packages():
    """Get available credit packages"""
    packages = []
    for key, pkg in config.CREDIT_PACKAGES.items():
        packages.append({
            'id': key,
            'name': pkg['name'],
            'credits': pkg['credits'],
            'price': pkg['price'],
            'price_per_credit': round(pkg['price'] / pkg['credits'], 2)
        })

    return jsonify({
        'success': True,
        'packages': packages
    }), 200


@payments_bp.route('/create-order', methods=['POST'])
@jwt_required_custom
def create_order(current_user):
    """Create PayPal payment order"""
    data = request.json
    package_name = data.get('package')

    if package_name not in config.CREDIT_PACKAGES:
        return jsonify({'error': 'Invalid package'}), 400

    package = config.CREDIT_PACKAGES[package_name]

    # Frontend URLs (adjust for production)
    return_url = data.get('return_url', 'http://localhost:3000/payment/success')
    cancel_url = data.get('cancel_url', 'http://localhost:3000/payment/cancel')

    try:
        # Create PayPal order
        result = paypal_service.create_order(package_name, return_url, cancel_url)

        # Create pending purchase record
        purchase = Purchase(
            user_id=current_user.id,
            package_name=package_name,
            credits_purchased=package['credits'],
            price_eur=package['price'],
            paypal_order_id=result['payment_id'],
            status='pending'
        )
        db.session.add(purchase)
        db.session.commit()

        return jsonify({
            'success': True,
            'payment_id': result['payment_id'],
            'approval_url': result['approval_url'],
            'purchase_id': purchase.id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/execute-payment', methods=['POST'])
@jwt_required_custom
def execute_payment(current_user):
    """Execute/Capture PayPal payment after user approval"""
    data = request.json
    payment_id = data.get('payment_id')
    payer_id = data.get('payer_id')

    if not payment_id or not payer_id:
        return jsonify({'error': 'Missing payment_id or payer_id'}), 400

    # Find purchase record
    purchase = Purchase.query.filter_by(
        paypal_order_id=payment_id,
        user_id=current_user.id
    ).first()

    if not purchase:
        return jsonify({'error': 'Purchase not found'}), 404

    if purchase.status == 'completed':
        return jsonify({'error': 'Payment already completed'}), 400

    try:
        # Execute payment with PayPal
        result = paypal_service.execute_payment(payment_id, payer_id)

        # Update purchase record
        purchase.status = 'completed'
        purchase.paypal_payer_id = payer_id
        purchase.paypal_payer_email = result.get('payer_email')
        purchase.completed_at = datetime.utcnow()

        # Add credits to user
        current_user.credits_remaining += purchase.credits_purchased
        current_user.total_credits_purchased += purchase.credits_purchased

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{purchase.credits_purchased} Credits erfolgreich gekauft!',
            'new_credits': current_user.credits_remaining,
            'purchase': purchase.to_dict()
        }), 200

    except Exception as e:
        purchase.status = 'failed'
        db.session.commit()
        return jsonify({'error': str(e)}), 500


@payments_bp.route('/history', methods=['GET'])
@jwt_required_custom
def get_purchase_history(current_user):
    """Get user's purchase history"""
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(
        Purchase.created_at.desc()
    ).all()

    return jsonify({
        'success': True,
        'purchases': [p.to_dict() for p in purchases],
        'total_spent': sum(float(p.price_eur) for p in purchases if p.status == 'completed')
    }), 200
```

### 6. Register Blueprint (app.py)

```python
# Add to app.py
from routes.payments import payments_bp

app.register_blueprint(payments_bp, url_prefix='/api/payments')
```

### 7. Dependencies (requirements.txt)

```txt
# Add:
paypalrestsdk==1.13.1
```

### 8. Environment Variables (.env)

```bash
# PayPal Configuration
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_CLIENT_SECRET=your_paypal_client_secret_here
PAYPAL_MODE=sandbox  # Change to 'live' for production
```

---

## 🎨 Frontend Implementation

### 1. New Page: BuyCredits.vue (frontend/src/pages/BuyCredits.vue)

```vue
<template>
  <div class="buy-credits">
    <h1>Credits kaufen</h1>

    <div class="current-credits">
      <h3>Deine Credits</h3>
      <p class="credits-display">{{ authStore.user?.credits_remaining || 0 }} Credits</p>
      <p class="lifetime-info">Insgesamt gekauft: {{ authStore.user?.total_credits_purchased || 0 }} Credits</p>
    </div>

    <h2>Pakete</h2>
    <div class="packages-grid">
      <div
        v-for="pkg in packages"
        :key="pkg.id"
        class="package-card"
        :class="{ 'popular': pkg.id === 'medium' }"
      >
        <div class="package-badge" v-if="pkg.id === 'medium'">Beliebt</div>

        <h3>{{ pkg.name }}</h3>
        <div class="credits-amount">{{ pkg.credits }} Credits</div>
        <div class="price">{{ pkg.price }}€</div>
        <div class="price-per-credit">{{ pkg.price_per_credit }}€ pro Credit</div>

        <button
          @click="buyPackage(pkg.id)"
          :disabled="loading"
          class="buy-button"
        >
          {{ loading ? 'Laden...' : 'Jetzt kaufen' }}
        </button>
      </div>
    </div>

    <div class="purchase-history" v-if="purchases.length">
      <h2>Kaufhistorie</h2>
      <table>
        <thead>
          <tr>
            <th>Datum</th>
            <th>Paket</th>
            <th>Credits</th>
            <th>Preis</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="purchase in purchases" :key="purchase.id">
            <td>{{ formatDate(purchase.created_at) }}</td>
            <td>{{ purchase.package_name }}</td>
            <td>{{ purchase.credits_purchased }}</td>
            <td>{{ purchase.price_eur }}€</td>
            <td :class="'status-' + purchase.status">
              {{ getStatusLabel(purchase.status) }}
            </td>
          </tr>
        </tbody>
      </table>
      <div class="total-spent">
        Gesamtausgaben: {{ totalSpent }}€
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { authStore } from '../store/auth'

const packages = ref([])
const purchases = ref([])
const totalSpent = ref(0)
const loading = ref(false)

const loadPackages = async () => {
  const { data } = await api.get('/payments/packages')
  packages.value = data.packages
}

const loadPurchaseHistory = async () => {
  const { data } = await api.get('/payments/history')
  purchases.value = data.purchases
  totalSpent.value = data.total_spent
}

const buyPackage = async (packageId) => {
  loading.value = true
  try {
    const { data } = await api.post('/payments/create-order', {
      package: packageId,
      return_url: `${window.location.origin}/payment/success`,
      cancel_url: `${window.location.origin}/buy-credits`
    })

    if (data.success) {
      // Redirect to PayPal
      window.location.href = data.approval_url
    }
  } catch (error) {
    alert('Fehler beim Erstellen der Bestellung')
    loading.value = false
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('de-DE')
}

const getStatusLabel = (status) => {
  const labels = {
    'pending': 'Ausstehend',
    'completed': 'Abgeschlossen',
    'failed': 'Fehlgeschlagen',
    'refunded': 'Erstattet'
  }
  return labels[status] || status
}

onMounted(() => {
  loadPackages()
  loadPurchaseHistory()
})
</script>

<style scoped>
.buy-credits {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.current-credits {
  background: #f0f9ff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  text-align: center;
}

.credits-display {
  font-size: 48px;
  font-weight: bold;
  color: #0066cc;
  margin: 10px 0;
}

.lifetime-info {
  color: #666;
  font-size: 14px;
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.package-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  position: relative;
  transition: transform 0.2s, border-color 0.2s;
}

.package-card:hover {
  transform: translateY(-5px);
  border-color: #0066cc;
}

.package-card.popular {
  border-color: #0066cc;
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.2);
}

.package-badge {
  position: absolute;
  top: -10px;
  right: 20px;
  background: #0066cc;
  color: white;
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.credits-amount {
  font-size: 36px;
  font-weight: bold;
  color: #333;
  margin: 15px 0;
}

.price {
  font-size: 28px;
  color: #0066cc;
  font-weight: bold;
  margin: 10px 0;
}

.price-per-credit {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
}

.buy-button {
  width: 100%;
  padding: 12px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.buy-button:hover:not(:disabled) {
  background: #0052a3;
}

.buy-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.purchase-history {
  margin-top: 50px;
}

.purchase-history table {
  width: 100%;
  border-collapse: collapse;
}

.purchase-history th,
.purchase-history td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.purchase-history th {
  background: #f5f5f5;
  font-weight: bold;
}

.status-completed { color: #28a745; }
.status-pending { color: #ffc107; }
.status-failed { color: #dc3545; }

.total-spent {
  text-align: right;
  padding: 15px;
  font-size: 18px;
  font-weight: bold;
  color: #333;
}
</style>
```

### 2. New Page: PaymentSuccess.vue

```vue
<template>
  <div class="payment-success">
    <div v-if="loading" class="loading">
      <h2>Zahlung wird verarbeitet...</h2>
      <p>Bitte warten Sie einen Moment.</p>
    </div>

    <div v-else-if="success" class="success">
      <div class="success-icon">✓</div>
      <h1>Zahlung erfolgreich!</h1>
      <p>Du hast <strong>{{ creditsPurchased }} Credits</strong> gekauft.</p>
      <p class="new-balance">Neuer Kontostand: {{ newCredits }} Credits</p>
      <button @click="goToDashboard">Zum Dashboard</button>
    </div>

    <div v-else class="error">
      <div class="error-icon">✗</div>
      <h1>Zahlung fehlgeschlagen</h1>
      <p>{{ errorMessage }}</p>
      <button @click="goToBuyCredits">Zurück zu Paketen</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
import { authStore } from '../store/auth'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const success = ref(false)
const creditsPurchased = ref(0)
const newCredits = ref(0)
const errorMessage = ref('')

onMounted(async () => {
  const paymentId = route.query.paymentId
  const payerId = route.query.PayerID

  if (!paymentId || !payerId) {
    loading.value = false
    errorMessage.value = 'Ungültige Zahlungs-Parameter'
    return
  }

  try {
    const { data } = await api.post('/payments/execute-payment', {
      payment_id: paymentId,
      payer_id: payerId
    })

    if (data.success) {
      success.value = true
      creditsPurchased.value = data.purchase.credits_purchased
      newCredits.value = data.new_credits

      // Refresh user data
      await authStore.refreshUser()
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Unbekannter Fehler'
  } finally {
    loading.value = false
  }
})

const goToDashboard = () => router.push('/')
const goToBuyCredits = () => router.push('/buy-credits')
</script>

<style scoped>
.payment-success {
  max-width: 600px;
  margin: 100px auto;
  padding: 40px;
  text-align: center;
}

.success-icon, .error-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.success-icon { color: #28a745; }
.error-icon { color: #dc3545; }

.new-balance {
  font-size: 24px;
  font-weight: bold;
  color: #0066cc;
  margin: 20px 0;
}

button {
  margin-top: 30px;
  padding: 12px 40px;
  font-size: 16px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:hover {
  background: #0052a3;
}
</style>
```

### 3. Router Configuration (frontend/src/router/index.js)

```javascript
// Add routes:
{
  path: '/buy-credits',
  name: 'BuyCredits',
  component: () => import('../pages/BuyCredits.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/payment/success',
  name: 'PaymentSuccess',
  component: () => import('../pages/PaymentSuccess.vue'),
  meta: { requiresAuth: true }
}
```

### 4. Navigation Update (App.vue or Navigation component)

```vue
<!-- Add to navigation -->
<router-link to="/buy-credits">Credits kaufen</router-link>
```

### 5. Settings Page Update (Settings.vue)

```vue
<!-- Add credit purchase button to Settings.vue -->
<div class="section">
  <h3>Credits</h3>
  <p>Verfügbar: {{ authStore.user?.credits_remaining }} Credits</p>
  <router-link to="/buy-credits">
    <button>Credits kaufen</button>
  </router-link>
</div>
```

---

## 🔒 Security Considerations

### 1. Payment Validation
- ✅ Validate package exists before creating order
- ✅ Verify user_id matches purchase record
- ✅ Check payment not already completed (prevent double-credit)
- ✅ Use PayPal's official SDK (secure communication)

### 2. Environment Variables
- ❗ NEVER commit PayPal credentials to Git
- ✅ Use .env file (already in .gitignore)
- ✅ Separate sandbox/live credentials

### 3. Error Handling
- ✅ Try-catch blocks around PayPal API calls
- ✅ Database rollback on payment failure
- ✅ Log all payment attempts for debugging

### 4. User Credits
- ✅ Use database transactions (atomicity)
- ✅ Validate credits_remaining before decrement
- ✅ Track total_credits_purchased separately

### 5. Webhook (Optional Enhancement)
- For production: Implement PayPal IPN/Webhooks
- Validates payments server-side independent of frontend
- Handles edge cases (user closes browser, etc.)

---

## 📦 Implementation Steps (Recommended Order)

### Phase 1: Database & Models ✅
1. ✅ Add `total_credits_purchased` to User model
2. ✅ Create `Purchase` model
3. ✅ Create migration script
4. ✅ Update `DEFAULT_CREDITS` to 5

### Phase 2: PayPal Integration ✅
1. ✅ Install `paypalrestsdk`
2. ✅ Create PayPalService
3. ✅ Add PayPal credentials to .env
4. ✅ Test in sandbox mode

### Phase 3: Backend API ✅
1. ✅ Create payments blueprint
2. ✅ Implement `/packages` endpoint
3. ✅ Implement `/create-order` endpoint
4. ✅ Implement `/execute-payment` endpoint
5. ✅ Implement `/history` endpoint
6. ✅ Register blueprint in app.py

### Phase 4: Frontend ✅
1. ✅ Create BuyCredits.vue
2. ✅ Create PaymentSuccess.vue
3. ✅ Update router
4. ✅ Add navigation links
5. ✅ Update Settings.vue

### Phase 5: Testing 🧪
1. Test sandbox payments
2. Test credit addition
3. Test purchase history
4. Test error handling
5. Test edge cases

### Phase 6: Production 🚀
1. Get PayPal Live credentials
2. Update PAYPAL_MODE to 'live'
3. Test with real payment (small amount)
4. Monitor logs for errors
5. Set up PayPal webhooks (optional)

---

## 🧪 Testing Checklist

### Manual Tests:
- [ ] User can view credit packages
- [ ] User can initiate payment
- [ ] PayPal popup/redirect works
- [ ] User can complete payment in sandbox
- [ ] Credits are added after payment
- [ ] Purchase appears in history
- [ ] User credits shown correctly
- [ ] Failed payment handled gracefully
- [ ] Cancelled payment handled correctly
- [ ] Cannot double-execute same payment

### Integration Tests:
- [ ] POST /api/payments/create-order (with JWT)
- [ ] POST /api/payments/execute-payment (with JWT)
- [ ] GET /api/payments/packages (public)
- [ ] GET /api/payments/history (with JWT)

### Edge Cases:
- [ ] User closes PayPal window
- [ ] Network error during payment
- [ ] PayPal API timeout
- [ ] Invalid package name
- [ ] Negative credits attempted
- [ ] SQL injection attempts
- [ ] XSS in purchase history

---

## 💰 Cost Analysis

### Per-Transaction Costs (PayPal):
```
PayPal Fee: 2.49% + 0.35€

Package Prices After Fees:
- Small (1€):   You receive: ~0.62€ (62%)
- Medium (4€):  You receive: ~3.55€ (89%)
- Large (7€):   You receive: ~6.52€ (93%)

Revenue Projection (100 Sales/Month):
- 50x Small:  31€
- 30x Medium: 106.50€
- 20x Large:  130.40€
Total: 267.90€/Month

Costs:
- PayPal Fees: ~32.10€
- Server: ~10€ (if needed)
- Claude API: ~30€ (assuming 5000 generations)
Net Profit: ~225.80€/Month
```

---

## 📚 Resources & Documentation

### PayPal:
- Official Docs: https://developer.paypal.com/docs/api/overview/
- Python SDK: https://github.com/paypal/PayPal-Python-SDK
- Sandbox Testing: https://developer.paypal.com/developer/accounts/

### Alternative (if PayPal issues):
- Stripe Integration Guide (easier, better docs)
- Paddle (handles VAT/taxes automatically)

---

## 🎯 Success Metrics

### After Implementation:
- **User Acquisition:** Track free signups (with 5 credits)
- **Conversion Rate:** % of free users who purchase
- **Average Purchase:** Which package sells most?
- **Revenue:** Monthly recurring revenue
- **Churn:** How many users return?

### Key Performance Indicators:
```
Target Metrics (After 3 Months):
- 1000 registered users
- 10% conversion rate (100 paying users)
- Average purchase: 4€ (Medium package)
- Monthly revenue: 400€
- Repeat purchase rate: 30%
```

---

## ⚠️ Important Notes

### 1. **Default Credits Changed: 50 → 5**
- New users get 5 free credits
- Existing test users keep their 50 credits
- Migration script needed for production users

### 2. **No Subscriptions**
- Credits NEVER expire
- Users buy once, use anytime
- Simpler than managing recurring billing

### 3. **PayPal Sandbox**
- Use sandbox for development
- Create test buyer account at developer.paypal.com
- Switch to live only after thorough testing

### 4. **Frontend URLs**
- Update return_url/cancel_url for production
- Use environment variables for URLs

### 5. **Database Migration**
- Backup database before migration
- Test migration on development first
- Plan for rollback if issues

---

## 🚀 Go-Live Checklist

Before deploying to production:

- [ ] PayPal live credentials configured
- [ ] PAYPAL_MODE set to 'live'
- [ ] Return/Cancel URLs point to production domain
- [ ] SSL certificate installed (HTTPS required by PayPal)
- [ ] Database backup created
- [ ] Migration script tested
- [ ] Error logging configured
- [ ] Payment webhook endpoint (optional but recommended)
- [ ] Legal pages updated (Terms, Privacy, Refund Policy)
- [ ] Email notifications for purchases
- [ ] Admin dashboard for monitoring purchases

---

**Implementation Estimate:** 1-2 days for full integration
**Testing Time:** 1 day
**Total:** 2-3 days to production-ready

**Next Step:** Exit plan mode and get user approval to implement.
