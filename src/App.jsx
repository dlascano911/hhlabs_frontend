import { useState, useEffect } from 'react';
import { HomePage } from './components/pages/HomePage';
import { CartPage } from './components/pages/CartPage';
import { PricingPage } from './components/pages/PricingPage';
import { ContactPage } from './components/pages/ContactPage';
import { DemoPage } from './components/demos/DemoPage';
import { TestSessionsPage } from './components/demos/TestSessionsPage';
import { trackingService } from './services/trackingService';
import './styles/App.css';

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

export default App;
