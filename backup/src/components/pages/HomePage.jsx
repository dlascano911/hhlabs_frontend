import { trackingService } from '../../services/trackingService';
import verbaImage from '../../assets/images/verba.png';
import '../../styles/pages/HomePage.css';

export function HomePage({ setCurrentPage }) {
  const scrollToSpecs = () => {
    const specsSection = document.getElementById('technical-specs');
    if (specsSection) {
      specsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
      trackingService.trackClick('view_specs');
    }
  };

  return (
    <div className="page home-page">
      <section className="hero">
        <div className="hero-wrapper">
          <div className="hero-content">
            <h1>Meet Verba</h1>
            <p className="subtitle">Your Pocket-Sized AI Companion</p>
            <p className="hero-description">Fast, private, and screen-light access to artificial intelligence. One button press. Speak naturally. Get instant answers. Verba removes the friction of smartphones, enabling AI access when your hands are busy or you want to stay focused.</p>
            <div className="hero-cta">
              <button className="btn-primary" onClick={() => { trackingService.trackClick('cta_preorder'); setCurrentPage('cart'); }}>Pre-Order Now</button>
              <button className="btn-secondary" onClick={scrollToSpecs}>Learn More</button>
            </div>
          </div>
          
          <div className="hero-device">
            <img src={verbaImage} alt="Verba AI Device" className="hero-device-image" />
          </div>
        </div>
      </section>

      <section className="features">
        <div className="feature-stripe">
          <div className="feature-content">
            <div className="feature-icon">⚡</div>
            <div className="feature-text">
              <h3>Instant Access</h3>
              <p>One button press. No unlocking. No apps. No distractions. Verba is always ready in your pocket, giving you instant AI access faster than reaching for your phone.</p>
            </div>
          </div>
        </div>

        <div className="feature-stripe alt">
          <div className="feature-content">
            <div className="feature-icon">🔒</div>
            <div className="feature-text">
              <h3>Privacy First</h3>
              <p>Press-to-talk only. Verba never listens unless you activate it. No passive recording. No camera. No data mining. Your conversations remain private, not stored or analyzed beyond your immediate request.</p>
            </div>
          </div>
        </div>

        <div className="feature-stripe">
          <div className="feature-content">
            <div className="feature-icon">🎯</div>
            <div className="feature-text">
              <h3>Designed for Real Life</h3>
              <p>Studying hands-free. Driving safely. Cooking in the kitchen. Verba works when your phone can't. Perfect for multitasking, with 20-40 minutes of daily use in short, focused interactions.</p>
            </div>
          </div>
        </div>

        <div className="feature-stripe alt">
          <div className="feature-content">
            <div className="feature-icon">🎨</div>
            <div className="feature-text">
              <h3>Simple & Customizable</h3>
              <p>Vintage-inspired design meets modern simplicity. Pocket-sized with organic, rounded form. Interchangeable buttons and color options let you make it yours. No complexity, just personality.</p>
            </div>
          </div>
        </div>

        <div className="feature-stripe">
          <div className="feature-content">
            <div className="feature-icon">💧</div>
            <div className="feature-text">
              <h3>Built to Last</h3>
              <p>IP67 water and dust resistant. Take Verba everywhere—from the shower to the trail. Designed for daily use with long battery life and durable construction that keeps up with your life.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="technical-specs-section" id="technical-specs">
        <div className="specs-container">
          <h2>Technical Specifications</h2>
          <table className="specs-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Verba</th>
                <th>Verba One</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Response Time</td>
                <td>&lt; 10 seconds</td>
                <td>&lt; 7 seconds</td>
              </tr>
              <tr>
                <td>Connectivity</td>
                <td>WiFi + Bluetooth</td>
                <td>WiFi + Bluetooth + PocketLink*</td>
              </tr>
              <tr>
                <td>Battery Life</td>
                <td>30 days**</td>
                <td>30 days**</td>
              </tr>
              <tr>
                <td>Memory</td>
                <td>4GB RAM</td>
                <td>8GB RAM</td>
              </tr>
              <tr>
                <td>Processor</td>
                <td>Snapdragon 680</td>
                <td>Snapdragon 782G</td>
              </tr>
              <tr>
                <td>Water Resistance</td>
                <td>IPX7 Certified</td>
                <td>IPX7 Certified</td>
              </tr>
            </tbody>
          </table>
          <p className="specs-note">* PocketLink: Our proprietary technology allowing device usage without WiFi</p>
          <p className="specs-note">** Using 20 minutes per day</p>
        </div>
      </section>
    </div>
  );
}
