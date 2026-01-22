import { useState, useEffect, useRef } from 'react';
import { audioService } from './services/audioService';
import { trackingService } from './services/trackingService';
import emailjs from '@emailjs/browser';
import verbaImage from './asset/images/verba.png';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  // Track page views
  useEffect(() => {
    trackingService.trackPageView(currentPage);
  }, [currentPage]);

  const handlePageChange = (page) => {
    trackingService.trackNavigation(currentPage, page);
    setCurrentPage(page);
  };

  const renderPage = () => {
    switch(currentPage) {
      case 'home':
        return <HomePage setCurrentPage={handlePageChange} />;
      case 'pricing':
        return <PricingPage setCurrentPage={handlePageChange} />;
      case 'contact':
        return <ContactPage />;
      case 'demo':
        return <DemoPage />;
      case 'test-sessions':
        return <TestSessionsPage />;
      case 'cart':
        return <CartPage />;
      default:
        return <HomePage setCurrentPage={handlePageChange} />;
    }
  };

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-container">
          <div className="logo" onClick={() => { trackingService.trackClick('logo'); handlePageChange('home'); }} style={{ cursor: 'pointer' }}>
            <span className="logo-product">Handheld Labs</span>
            <span className="logo-company">California</span>
          </div>
          <ul className="nav-links">
            <li><a onClick={() => { trackingService.trackClick('nav_home'); handlePageChange('home'); }} className={currentPage === 'home' ? 'active' : ''}>Home</a></li>
            <li><a onClick={() => { trackingService.trackClick('nav_pricing'); handlePageChange('pricing'); }} className={currentPage === 'pricing' ? 'active' : ''}>Pricing</a></li>
            <li><a onClick={() => { trackingService.trackClick('nav_contact'); handlePageChange('contact'); }} className={currentPage === 'contact' ? 'active' : ''}>Contact</a></li>
            <li><a onClick={() => { trackingService.trackClick('nav_demo'); handlePageChange('demo'); }} className={currentPage === 'demo' ? 'active demo-link' : 'demo-link'}>Demo</a></li>
            <li><a onClick={() => { trackingService.trackClick('nav_test_sessions'); handlePageChange('test-sessions'); }} className={currentPage === 'test-sessions' ? 'active demo-link' : 'demo-link'}>Test Sessions</a></li>
            <li><a href="/debug-sessions.html" target="_blank" onClick={() => trackingService.trackClick('nav_debug_sessions')} className="demo-link">Debug Sessions</a></li>
          </ul>
        </div>
      </nav>
      {renderPage()}
      {currentPage !== 'test-sessions' && <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h3>Handheld Labs</h3>
            <p>California</p>
          </div>
          <div className="footer-section">
            <p>Email: <a href="mailto:info@handheldlabs.com">info@handheldlabs.com</a></p>
          </div>
          <div className="footer-section">
            <p>&copy; {new Date().getFullYear()} Handheld Labs. All rights reserved.</p>
          </div>
        </div>
      </footer>}
    </div>
  );
}

function HomePage({ setCurrentPage }) {
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

function CartPage() {
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
                const productName = `${selectedDevice.name}_${selectedPlan.name}`;
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
                  const productName = `${selectedDevice.name}_${selectedPlan.name}`;
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

function PricingPage({ setCurrentPage }) {
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

function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [status, setStatus] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatus('Sending...');

    try {
      // Track contact form submission
      trackingService.trackContact();
      
      // Enviar email usando EmailJS
      const templateParams = {
        to_email: 'diego@handheldlabs.com',
        cc_email: 'dlascano91@gmail.com',
        from_name: formData.name,
        from_email: formData.email,
        message: formData.message,
        reply_to: formData.email
      };

      // Nota: Necesitas configurar EmailJS con tu Service ID, Template ID y Public Key
      // Por ahora, simularemos el envío con un POST a un endpoint
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to: 'diego@handheldlabs.com',
          cc: 'dlascano91@gmail.com',
          from_name: formData.name,
          from_email: formData.email,
          message: formData.message
        })
      }).catch(() => null);

      setStatus('Thank you for your message! We will get back to you soon.');
      setFormData({ name: '', email: '', message: '' });
      
      setTimeout(() => setStatus(''), 5000);
    } catch (error) {
      console.error('Error sending email:', error);
      setStatus('There was an error sending your message. Please try emailing us directly at diego@handheldlabs.com');
      setTimeout(() => setStatus(''), 5000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="page contact-page">
      <section className="contact-hero">
        <h1>Get in Touch</h1>
        <p>Have questions? We'd love to hear from you.</p>
      </section>

      <div className="contact-container">
        <form className="contact-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="message">Message</label>
            <textarea
              id="message"
              name="message"
              rows="6"
              value={formData.message}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            ></textarea>
          </div>

          <button type="submit" className="btn-submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sending...' : 'Send Message'}
          </button>
          
          {status && (
            <div className={`form-status ${status.includes('error') || status.includes('Error') ? 'error' : 'success'}`}>
              {status}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [timings, setTimings] = useState({ transcript: null, gemini: null, tts: null });
  const [transcription, setTranscription] = useState('');
  const [geminiResponse, setGeminiResponse] = useState('');
  const [responseAudioUrl, setResponseAudioUrl] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const audioRef = useRef(null);
  
  // Reproducir automáticamente cuando se crea nuevo audio
  useEffect(() => {
    if (responseAudioUrl && audioRef.current) {
      audioRef.current.play().catch(err => console.log('Error al reproducir audio:', err));
    }
  }, [responseAudioUrl]);
  
  // Generar UUID v4 simple
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };
  
  const [sessionId, setSessionId] = useState(() => generateUUID());  // Generar session_id inicial

  // Iniciar grabación
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => {
        chunks.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        await processAudioFile(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setAudioChunks(chunks);
    } catch (err) {
      setError(`Error accediendo al micrófono: ${err.message}`);
    }
  };

  // Detener grabación
  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // Manejar subida de archivo
  const handleAudioUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    await processAudioFile(file);
  };

  // Procesar archivo de audio (flujo completo)
  const processAudioFile = async (audioFile) => {
    trackingService.trackDemo();

    setLoading(true);
    setError('');
    setTranscription('');
    setGeminiResponse('');
    setResponseAudioUrl(null);
    setTimings({ transcript: null, gemini: null, tts: null });

    try {
      // Fase 1: Transcribir audio a texto
      const t1 = performance.now();
      const transcriptResult = await audioService.audioToText(audioFile);
      const t2 = performance.now();
      const transcriptTime = Math.round(t2 - t1);
      
      setTranscription(transcriptResult.text);
      setTimings(prev => ({ ...prev, transcript: transcriptTime }));

      // Extraer idioma detectado por Whisper
      const detectedLanguage = transcriptResult.language_info?.code || transcriptResult.language || 'en';
      console.log('🌐 Idioma detectado:', detectedLanguage, transcriptResult.language_info);

      // Fase 2: Enviar a Gemini con el idioma detectado y session_id
      const t3 = performance.now();
      const API_URL = import.meta.env.VITE_WRAPPER_API_URL || 'https://handheldlabs-backend-45973956798.us-central1.run.app';
      const geminiResponse = await fetch(`${API_URL}/process-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: transcriptResult.text,
          language: detectedLanguage,  // ← Pasar idioma detectado
          session_id: sessionId  // ← Pasar session_id (null en primera llamada)
        })
      });

      if (!geminiResponse.ok) {
        throw new Error(`Error en Gemini: ${geminiResponse.status}`);
      }

      const geminiData = await geminiResponse.json();
      const t4 = performance.now();
      const geminiTime = Math.round(t4 - t3);
      
      setGeminiResponse(geminiData.response);
      setTimings(prev => ({ ...prev, gemini: geminiTime }));

      // Guardar session_id retornado por el backend
      if (geminiData.session_id) {
        setSessionId(geminiData.session_id);
        console.log('🔑 Session ID actualizado:', geminiData.session_id);
      }

      // Fase 3: Convertir respuesta de Gemini a audio usando el idioma detectado
      const t5 = performance.now();
      const ttsResult = await audioService.textToAudio(geminiData.response, detectedLanguage);
      const t6 = performance.now();
      const ttsTime = Math.round(t6 - t5);
      
      // Convertir base64 a Blob y crear URL
      const audioBlob = await fetch(`data:audio/wav;base64,${ttsResult.audio_base64}`).then(res => res.blob());
      const url = URL.createObjectURL(audioBlob);
      setResponseAudioUrl(url);
      setTimings(prev => ({ ...prev, tts: ttsTime }));

    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setTranscription('');
    setGeminiResponse('');
    setResponseAudioUrl(null);
    setError('');
    setTimings({ transcript: null, gemini: null, tts: null });
    setSessionId(generateUUID());  // Generar nuevo session_id para nueva sesión
  };

  return (
    <div className="page demo-page">
      <div className="demo-container">
        <div className="demo-card">
          <h1 className="demo-title">🎤 Verba Audio Demo</h1>
          <p className="demo-subtitle">Graba o sube audio → Transcripción → Gemini → Audio</p>

          {(timings.transcript || timings.gemini || timings.tts) && (
            <div className="timings-box">
              {timings.transcript && <p>⏱️ Transcripción: {timings.transcript}ms</p>}
              {timings.gemini && <p>⏱️ Gemini: {timings.gemini}ms</p>}
              {timings.tts && <p>⏱️ TTS: {timings.tts}ms</p>}
              {timings.transcript && timings.gemini && timings.tts && (
                <p><strong>⏱️ Total: {timings.transcript + timings.gemini + timings.tts}ms</strong></p>
              )}
            </div>
          )}

          <div className="demo-input-section">
            <div className="demo-controls" style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <button 
                onClick={isRecording ? stopRecording : startRecording}
                disabled={loading}
                className="btn-process"
                style={{ flex: 1 }}
              >
                {isRecording ? '⏹️ Detener Grabación' : '🎤 Grabar Audio'}
              </button>
              
              <label 
                htmlFor="audio-upload" 
                className="btn-process"
                style={{ 
                  flex: 1, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.5 : 1
                }}
              >
                📤 Subir Audio
              </label>
              <input
                id="audio-upload"
                type="file"
                accept="audio/*"
                onChange={handleAudioUpload}
                disabled={loading}
                style={{ display: 'none' }}
              />
            </div>

            {loading && (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <p>⏳ Procesando...</p>
              </div>
            )}
          </div>

          {transcription && (
            <div className="result-box" style={{ marginTop: '20px' }}>
              <h3>📝 Transcripción</h3>
              <p>{transcription}</p>
            </div>
          )}

          {geminiResponse && (
            <div className="result-box gemini" style={{ marginTop: '20px' }}>
              <div className="gemini-header">
                <h3>🤖 Respuesta de Gemini</h3>
                {timings.gemini && timings.tts && (
                  <span className="gemini-timing">
                    Gemini: {timings.gemini}ms | Audio: {timings.tts}ms
                  </span>
                )}
              </div>
              <p>{geminiResponse}</p>
            </div>
          )}

          {responseAudioUrl && (
            <div className="result-box" style={{ marginTop: '20px' }}>
              <h3>🔊 Audio de la Respuesta</h3>
              <audio ref={audioRef} controls src={responseAudioUrl} style={{ width: '100%', marginTop: '10px' }} />
              <button onClick={handleReset} className="btn-reset" style={{ marginTop: '15px' }}>
                Nueva Consulta
              </button>
            </div>
          )}

          {error && (
            <div className="error-box">
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TestSessionsPage() {
  // Generar UUID v4 simple
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };

  const [sessionId, setSessionId] = useState(() => generateUUID());
  const [messageCount, setMessageCount] = useState(0);
  const [topicChangeCount, setTopicChangeCount] = useState(0);
  const [responseTimes, setResponseTimes] = useState([]);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const chatAreaRef = useRef(null);

  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const addMessage = (type, text, time = null, topicChanged = false) => {
    const now = new Date().toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });

    setMessages(prev => [...prev, {
      type,
      text,
      time,
      topicChanged,
      timestamp: now
    }]);
  };

  const sendMessage = async () => {
    const message = userInput.trim();
    if (!message) return;

    setIsLoading(true);
    setUserInput('');

    addMessage('user', message);

    try {
      const startTime = performance.now();
      const API_URL = import.meta.env.VITE_WRAPPER_API_URL || 'https://handheldlabs-backend-45973956798.us-central1.run.app';

      const response = await fetch(`${API_URL}/process-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: message,
          language: 'es',
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);

      // Actualizar session_id y detectar cambio de tema
      if (data.session_id) {
        const isNewSession = sessionId !== data.session_id;
        setSessionId(data.session_id);
        
        if (isNewSession && messageCount > 0) {
          setTopicChangeCount(prev => prev + 1);
        }
      }

      addMessage('assistant', data.response, responseTime, data.topic_changed);

      setMessageCount(prev => prev + 1);
      setResponseTimes(prev => [...prev, responseTime]);

      setConversationHistory(prev => [...prev, {
        timestamp: new Date().toISOString(),
        user: message,
        assistant: data.response,
        sessionId: data.session_id,
        responseTime: responseTime
      }]);

    } catch (error) {
      console.error('Error:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      sendMessage();
    }
  };

  const resetSession = () => {
    if (!confirm('¿Estás seguro de que quieres reiniciar la sesión?')) return;

    setSessionId(generateUUID());  // Generar nuevo UUID en lugar de null
    setMessageCount(0);
    setTopicChangeCount(0);
    setResponseTimes([]);
    setConversationHistory([]);
    setMessages([]);
  };

  const exportConversation = () => {
    if (conversationHistory.length === 0) {
      alert('No hay conversación para exportar');
      return;
    }

    const exportData = {
      sessionId: sessionId,
      messageCount: messageCount,
      topicChanges: topicChangeCount,
      averageResponseTime: responseTimes.length > 0 
        ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
        : 0,
      conversation: conversationHistory,
      exportedAt: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
      type: 'application/json' 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${sessionId?.substring(0, 8)}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    alert('✅ Conversación exportada exitosamente');
  };

  const runTestScenario = async (scenario) => {
    const scenarios = {
      'same-topic': [
        '¿Sabes sobre Roma?',
        'Quiero ir de vacaciones',
        '¿Qué pizza me recomiendas?',
        '¿Cuánto cuesta el vuelo?'
      ],
      'topic-change': [
        '¿Sabes sobre Roma?',
        'Quiero ir de vacaciones',
        '¿Cuántas patas tiene una araña?',
        '¿Dónde viven las arañas?'
      ],
      'multi-lang': [
        'Hola, ¿cómo estás?',
        'Hello, how are you?',
        'Bonjour, comment allez-vous?',
        '¿Me puedes ayudar en español?'
      ],
      'context-test': [
        'Quiero ir a Italia',
        '¿Cuánto cuesta?',
        '¿Y el hotel?',
        '¿Qué documentos necesito?'
      ]
    };

    const scenarioMessages = scenarios[scenario];
    if (!scenarioMessages) return;

    for (let i = 0; i < scenarioMessages.length; i++) {
      setUserInput(scenarioMessages[i]);
      await new Promise(resolve => setTimeout(resolve, 100));
      await sendMessage();
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  };

  const avgTime = responseTimes.length > 0 
    ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
    : 0;

  const lastTime = responseTimes.length > 0 ? responseTimes[responseTimes.length - 1] : 0;
  const maxTime = 5000;
  const percentage = Math.min((lastTime / maxTime) * 100, 100);

  return (
    <div className="page test-sessions-page">
      <div className="test-sessions-container">
        <div className="test-main-panel">
          <div className="test-header">
            <h1>🧪 Test de Sesiones Conversacionales</h1>
            <p>Prueba el sistema de gestión de contexto y detección de cambio de tema</p>
            <div className="test-session-info">
              <div>
                <strong>Session ID:</strong>{' '}
                <span className="test-session-id">
                  {sessionId ? `${sessionId.substring(0, 8)}...${sessionId.substring(sessionId.length - 8)}` : 'Sin sesión activa'}
                </span>
              </div>
              <div>
                <strong>Mensajes:</strong> <span>{messageCount}</span>
              </div>
            </div>
          </div>

          <div className="test-chat-area" ref={chatAreaRef}>
            {messages.length === 0 ? (
              <div className="test-empty-state">
                <div className="test-empty-icon">💬</div>
                <h3>Comienza una conversación</h3>
                <p>Escribe un mensaje para iniciar la sesión</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className="test-message">
                  <div className="test-message-header">
                    {msg.type === 'user' && <span className="test-badge">TÚ</span>}
                    {msg.type === 'assistant' && (
                      <>
                        <span className="test-badge">VERBA AI</span>
                        {msg.topicChanged && <span className="test-topic-badge">🔄 Cambio de tema</span>}
                      </>
                    )}
                  </div>
                  <div className={`test-message-${msg.type}`}>
                    {msg.text}
                    <div className="test-message-time">
                      {msg.time && <span>⏱️ {msg.time}ms</span>}
                      <span>🕐 {msg.timestamp}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="test-input-area">
            <input
              type="text"
              className="test-input-field"
              placeholder="Escribe tu mensaje aquí..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
            />
            <button 
              className="test-btn-send" 
              onClick={sendMessage}
              disabled={isLoading}
            >
              {isLoading ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </div>

        <div className="test-sidebar">
          <div className="test-stats-panel">
            <h2>📊 Estadísticas</h2>
            
            <div className="test-stat-item">
              <div className="test-stat-label">Total de Mensajes</div>
              <div className="test-stat-value">{messageCount}</div>
            </div>

            <div className="test-stat-item">
              <div className="test-stat-label">Cambios de Tema</div>
              <div className="test-stat-value">{topicChangeCount}</div>
            </div>

            <div className="test-stat-item">
              <div className="test-stat-label">Tiempo Promedio</div>
              <div className="test-stat-value">{avgTime > 0 ? `${avgTime}ms` : '—'}</div>
            </div>

            {lastTime > 0 && (
              <div className="test-performance">
                <strong>⚡ Último Tiempo</strong>
                <div className="test-chart-bar">
                  <div className="test-chart-fill" style={{ width: `${percentage}%` }}>
                    {lastTime}ms
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="test-controls-panel">
            <h2>🎮 Controles</h2>
            
            <button className="test-control-btn test-btn-reset" onClick={resetSession}>
              🔄 Reiniciar Sesión
            </button>

            <button className="test-control-btn test-btn-export" onClick={exportConversation}>
              💾 Exportar Conversación
            </button>

            <div className="test-scenarios">
              <strong>🧪 Escenarios de Prueba</strong>
              
              <div className="test-scenario" onClick={() => runTestScenario('same-topic')}>
                ✅ Mismo Tema (Viajes a Roma)
              </div>
              
              <div className="test-scenario" onClick={() => runTestScenario('topic-change')}>
                🔄 Cambio de Tema (Roma → Arañas)
              </div>
              
              <div className="test-scenario" onClick={() => runTestScenario('multi-lang')}>
                🌍 Multi-idioma (ES → EN)
              </div>

              <div className="test-scenario" onClick={() => runTestScenario('context-test')}>
                📚 Test de Contexto (Preguntas ambiguas)
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
