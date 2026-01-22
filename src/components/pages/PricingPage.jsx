import { trackingService } from '../../services/trackingService';
import '../../styles/pages/PricingPage.css';

export function PricingPage({ setCurrentPage }) {
  return (
    <div className="page pricing-page">
      <section className="pricing-hero">
        <h1>Choose Your Plan</h1>
        <p>Plans are per device. Start free with your purchase.</p>
      </section>

      <div className="pricing-cards">
        <div className="pricing-card">
          <div className="plan-header">
            <h3>Base</h3>
            <div className="price">
              <span className="amount-free">Free</span>
            </div>
            <p className="plan-subtitle">Includes 3 Months of Standard Plan for free</p>
          </div>
          <ul className="plan-features">
            <li>✓ 15 minutes per day</li>
            <li>✓ General AI access</li>
            <li>✓ Standard audio output</li>
            <li>✓ Basic configuration</li>
          </ul>
          <button className="btn-plan" onClick={() => setCurrentPage('cart')}>Buy</button>
        </div>

        <div className="pricing-card featured">
          <div className="popular-badge">Most Popular</div>
          <div className="plan-header">
            <h3>Standard <span className="discount-badge">17% Off</span></h3>
            <div className="price">
              <span className="currency">$</span>
              <span className="amount">2.99</span>
              <span className="period">/month</span>
            </div>
            <p className="plan-subtitle">Billed $29.99 annually</p>
          </div>
          <ul className="plan-features">
            <li>✓ Unlimited conversations</li>
            <li>✓ General AI access</li>
            <li>✓ Standard audio output</li>
            <li>✓ Standard configuration</li>
          </ul>
          <button className="btn-plan primary" onClick={() => setCurrentPage('cart')}>Buy</button>
        </div>

        <div className="pricing-card">
          <div className="plan-header">
            <h3>Premium <span className="discount-badge">17% Off</span></h3>
            <div className="price">
              <span className="currency">$</span>
              <span className="amount">4.99</span>
              <span className="period">/month</span>
            </div>
            <p className="plan-subtitle">Billed $49.99 annually</p>
          </div>
          <ul className="plan-features">
            <li>✓ Unlimited conversations</li>
            <li>✓ Premium audio compression</li>
            <li>✓ Advanced configuration</li>
            <li>✓ AI Profiles: Coaching</li>
            <li>✓ AI Profiles: Health Advisor</li>
            <li>✓ AI Profiles: Chef</li>
          </ul>
          <button className="btn-plan" onClick={() => setCurrentPage('cart')}>Buy</button>
        </div>
      </div>
    </div>
  );
}
