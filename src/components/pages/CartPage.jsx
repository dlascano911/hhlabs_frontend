import { useState } from 'react';
import { trackingService } from '../../services/trackingService';
import '../../styles/pages/CartPage.css';

export function CartPage() {
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [step, setStep] = useState(1);

  const devices = [
    {
      id: 'verba',
      name: 'Verba',
      price: 45,
      features: ['WiFi', 'IPX7 Water Resistant', 'Standard Audio', '4GB RAM', 'Snapdragon 680']
    },
    {
      id: 'verba-one',
      name: 'Verba One',
      price: 65,
      features: ['WiFi', 'eSIM Support', 'IPX7 Water Resistant', 'Enhanced Audio', '8GB RAM', 'Snapdragon 782G']
    }
  ];

  const plans = [
    {
      id: 'basic-plus',
      name: 'Basic',
      monthlyPrice: 0,
      annualPrice: 0,
      discount: null,
      note: 'Includes 3 Months of Standard Plan for free',
      features: ['15 min/day for 3 months', 'Then unlimited Standard', 'Annual commitment']
    },
    {
      id: 'standard-annual',
      name: 'Standard Annual',
      monthlyPrice: 2.99,
      annualPrice: 29.99,
      discount: '17% Off',
      features: ['Unlimited conversations', 'Standard audio', 'Annual billing']
    },
    {
      id: 'premium-annual',
      name: 'Premium Annual',
      monthlyPrice: 4.99,
      annualPrice: 49.99,
      discount: '17% Off',
      features: ['Everything in Standard', 'Premium audio', 'AI Profiles', 'Annual billing']
    }
  ];

  const [shippingInfo, setShippingInfo] = useState({
    fullName: '',
    email: '',
    address: '',
    city: '',
    state: '',
    zip: '',
    country: 'USA'
  });

  const [paymentMethod, setPaymentMethod] = useState('card');

  const handleDeviceSelect = (deviceId) => {
    setSelectedDevice(deviceId);
    setStep(2);
  };

  const handlePlanSelect = (planId) => {
    setSelectedPlan(planId);
    setStep(3);
  };

  const getTotalPrice = () => {
    const device = devices.find(d => d.id === selectedDevice);
    const plan = plans.find(p => p.id === selectedPlan);
    if (!device) return 0;
    return device.price + (plan ? plan.annualPrice : 0);
  };

  return (
    <div className="page cart-page">
      <div className="cart-container">
        <h1>Complete Your Order</h1>
        
        <div className="progress-steps">
          <div className={`progress-step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            <span className="step-number">1</span>
            <span className="step-label">Device</span>
          </div>
          <div className={`progress-step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''} ${!selectedDevice ? 'disabled' : ''}`}>
            <span className="step-number">2</span>
            <span className="step-label">Plan</span>
          </div>
          <div className={`progress-step ${step >= 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''} ${!selectedPlan ? 'disabled' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-label">Shipping</span>
          </div>
          <div className={`progress-step ${step >= 4 ? 'active' : ''} ${!selectedPlan ? 'disabled' : ''}`}>
            <span className="step-number">4</span>
            <span className="step-label">Payment</span>
          </div>
        </div>

        {step === 1 && (
          <div className="cart-section">
            <h2>Choose Your Device</h2>
            <div className="device-cards">
              {devices.map(device => (
                <div 
                  key={device.id}
                  className={`device-card ${selectedDevice === device.id ? 'selected' : ''}`}
                  onClick={() => handleDeviceSelect(device.id)}
                >
                  <h3>{device.name}</h3>
                  <div className="device-price">${device.price}</div>
                  <ul className="device-features">
                    {device.features.map((feature, idx) => (
                      <li key={idx}>✓ {feature}</li>
                    ))}
                  </ul>
                  <button className="btn-select">
                    {selectedDevice === device.id ? 'Selected' : 'Select'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="cart-section">
            <h2>Choose Your Plan</h2>
            <p className="section-subtitle">All plans are billed annually</p>
            <div className="plan-cards">
              {plans.map(plan => (
                <div 
                  key={plan.id}
                  className={`plan-card ${selectedPlan === plan.id ? 'selected' : ''}`}
                  onClick={() => handlePlanSelect(plan.id)}
                >
                  <h3>
                    {plan.name}
                    {plan.discount && <span className="plan-discount-inline">{plan.discount}</span>}
                  </h3>
                  <div className="plan-pricing">
                    {plan.monthlyPrice === 0 ? (
                      <div className="plan-free">Free</div>
                    ) : (
                      <>
                        <div className="plan-monthly-large">${plan.monthlyPrice}/month</div>
                        <div className="plan-annual-note">Billed ${plan.annualPrice} annually</div>
                      </>
                    )}
                  </div>
                  <ul className="plan-features-list">
                    {plan.features.map((feature, idx) => (
                      <li key={idx}>{feature}</li>
                    ))}
                  </ul>
                  <button className="btn-select">
                    {selectedPlan === plan.id ? 'Selected' : 'Select'}
                  </button>
                  {plan.note && <div className="plan-note">{plan.note}</div>}
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="cart-section">
            <h2>Shipping Information</h2>
            <form className="shipping-form" onSubmit={(e) => { e.preventDefault(); setStep(4); }}>
              <div className="form-row">
                <input
                  type="text"
                  placeholder="Full Name"
                  value={shippingInfo.fullName}
                  onChange={(e) => setShippingInfo({...shippingInfo, fullName: e.target.value})}
                  required
                />
              </div>
              <div className="form-row">
                <input
                  type="email"
                  placeholder="Email"
                  value={shippingInfo.email}
                  onChange={(e) => setShippingInfo({...shippingInfo, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-row">
                <input
                  type="text"
                  placeholder="Street Address"
                  value={shippingInfo.address}
                  onChange={(e) => setShippingInfo({...shippingInfo, address: e.target.value})}
                  required
                />
              </div>
              <div className="form-row-group">
                <input
                  type="text"
                  placeholder="City"
                  value={shippingInfo.city}
                  onChange={(e) => setShippingInfo({...shippingInfo, city: e.target.value})}
                  required
                />
                <input
                  type="text"
                  placeholder="State"
                  value={shippingInfo.state}
                  onChange={(e) => setShippingInfo({...shippingInfo, state: e.target.value})}
                  required
                />
                <input
                  type="text"
                  placeholder="ZIP"
                  value={shippingInfo.zip}
                  onChange={(e) => setShippingInfo({...shippingInfo, zip: e.target.value})}
                  required
                />
              </div>
              <button type="submit" className="btn-primary">Continue to Payment</button>
            </form>
          </div>
        )}

        {step === 4 && (
          <div className="cart-section">
            <h2>Payment</h2>
            <div className="payment-methods">
              <button 
                className={`payment-method ${paymentMethod === 'card' ? 'active' : ''}`}
                onClick={() => setPaymentMethod('card')}
              >
                💳 Credit Card
              </button>
              <button 
                className={`payment-method ${paymentMethod === 'paypal' ? 'active' : ''}`}
                onClick={() => setPaymentMethod('paypal')}
              >
                🅿️ PayPal
              </button>
            </div>

            {paymentMethod === 'card' && (
              <form className="payment-form" onSubmit={(e) => { 
                e.preventDefault(); 
                const productName = `${selectedDevice}_${selectedPlan}`;
                trackingService.trackPurchase(productName);
                alert('Order placed!'); 
              }}>
                <input type="text" placeholder="Card Number" required />
                <div className="form-row-group">
                  <input type="text" placeholder="MM/YY" required />
                  <input type="text" placeholder="CVV" required />
                </div>
                <input type="text" placeholder="Cardholder Name" required />
                <button type="submit" className="btn-primary">Place Order - ${getTotalPrice()}</button>
              </form>
            )}

            {paymentMethod === 'paypal' && (
              <div className="paypal-checkout">
                <button className="btn-paypal" onClick={() => {
                  const productName = `${selectedDevice}_${selectedPlan}`;
                  trackingService.trackPurchase(productName);
                }}>Continue with PayPal</button>
                <p className="payment-note">You'll be redirected to PayPal to complete your purchase</p>
              </div>
            )}
          </div>
        )}

        <div className="order-summary">
          <h3>Order Summary</h3>
          {selectedDevice && (
            <div className="summary-item">
              <span>{devices.find(d => d.id === selectedDevice)?.name}</span>
              <span>${devices.find(d => d.id === selectedDevice)?.price}</span>
            </div>
          )}
          {selectedPlan && (
            <div className="summary-item">
              <span>{plans.find(p => p.id === selectedPlan)?.name}</span>
              <span>${plans.find(p => p.id === selectedPlan)?.annualPrice}/year</span>
            </div>
          )}
          <div className="summary-total">
            <span>Total</span>
            <span>${getTotalPrice()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
