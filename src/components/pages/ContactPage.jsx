import { useState } from 'react';
import { trackingService } from '../../services/trackingService';
import '../../styles/pages/ContactPage.css';

export function ContactPage() {
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
      
      // Send message to backend contact endpoint
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
