// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80, // Offset for the fixed header
                behavior: 'smooth'
            });
        }
    });
});

// Add active class to header on scroll
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
    if (window.scrollY > 0) {
        header.classList.add('active');
    } else {
        header.classList.remove('active');
    }
});

// Simple animation for elements when they come into view
const animateOnScroll = () => {
    const elements = document.querySelectorAll('.feature-content, .feature-image, .cta h2, .trust-badges, .testimonial');
    
    elements.forEach(element => {
        const elementPosition = element.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (elementPosition < windowHeight - 100) {
            element.classList.add('visible');
        }
    });
};

// Add the CSS classes for animations
document.addEventListener('DOMContentLoaded', () => {
    // Add animation classes
    const style = document.createElement('style');
    style.textContent = `
        .feature-content, .feature-image, .cta h2, .trust-badges, .testimonial {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .feature-content.visible, .feature-image.visible, .cta h2.visible, .trust-badges.visible, .testimonial.visible {
            opacity: 1;
            transform: translateY(0);
        }
    `;
    document.head.appendChild(style);
    
    // Initial check for elements in view
    animateOnScroll();
    
    // Check again on scroll
    window.addEventListener('scroll', animateOnScroll);
});

// Mobile menu toggle functionality
const createMobileMenu = () => {
    const nav = document.querySelector('.nav');
    const header = document.querySelector('.header .container');
    
    // Only add mobile menu if it's not already there
    if (!document.querySelector('.mobile-menu-toggle')) {
        // Create mobile menu toggle button
        const mobileMenuToggle = document.createElement('button');
        mobileMenuToggle.classList.add('mobile-menu-toggle');
        mobileMenuToggle.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;
        
        // Add toggle button to header
        header.appendChild(mobileMenuToggle);
        
        // Add functionality to toggle button
        mobileMenuToggle.addEventListener('click', () => {
            nav.classList.toggle('active');
            mobileMenuToggle.classList.toggle('active');
        });
        
        // Add CSS for mobile menu
        const style = document.createElement('style');
        style.textContent = `
            @media (max-width: 767px) {
                .nav {
                    position: fixed;
                    top: 70px;
                    left: 0;
                    width: 100%;
                    background: white;
                    flex-direction: column;
                    padding: 1.5rem;
                    box-shadow: var(--shadow);
                    transform: translateY(-100%);
                    opacity: 0;
                    visibility: hidden;
                    transition: all 0.3s ease;
                    z-index: 99;
                }
                
                .nav.active {
                    transform: translateY(0);
                    opacity: 1;
                    visibility: visible;
                }
                
                .nav a {
                    padding: 1rem 0;
                    font-size: 1.25rem;
                    border-bottom: 1px solid var(--border-color);
                    width: 100%;
                    text-align: center;
                }
                
                .mobile-menu-toggle {
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    width: 30px;
                    height: 21px;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    padding: 0;
                    z-index: 10;
                }
                
                .mobile-menu-toggle span {
                    display: block;
                    width: 100%;
                    height: 3px;
                    background: var(--text-color);
                    border-radius: 3px;
                    transition: all 0.3s ease;
                }
                
                .mobile-menu-toggle.active span:nth-child(1) {
                    transform: translateY(9px) rotate(45deg);
                }
                
                .mobile-menu-toggle.active span:nth-child(2) {
                    opacity: 0;
                }
                
                .mobile-menu-toggle.active span:nth-child(3) {
                    transform: translateY(-9px) rotate(-45deg);
                }
            }
            
            @media (min-width: 768px) {
                .mobile-menu-toggle {
                    display: none;
                }
            }
        `;
        document.head.appendChild(style);
    }
};

// Create mobile menu on load
document.addEventListener('DOMContentLoaded', createMobileMenu);

// Add a simple download button click handler
document.addEventListener('DOMContentLoaded', () => {
    const downloadButtons = document.querySelectorAll('.btn-primary');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            // Prevent default behavior if it's just a placeholder link
            if (button.getAttribute('href') === '#' || button.getAttribute('href') === '#download') {
                e.preventDefault();
                
                // Show a coming soon message
                const message = document.createElement('div');
                message.classList.add('download-message');
                message.innerHTML = `
                    <div class="download-popup">
                        <h3>Coming Soon!</h3>
                        <p>Our app is currently in final testing. Enter your email to be notified when we launch:</p>
                        <form class="notify-form">
                            <input type="email" placeholder="Your email address" required>
                            <button type="submit" class="btn btn-primary">Notify Me</button>
                        </form>
                        <button class="close-popup">×</button>
                    </div>
                `;
                
                document.body.appendChild(message);
                
                // Add CSS for popup
                const style = document.createElement('style');
                style.textContent = `
                    .download-message {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0, 0, 0, 0.5);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 1000;
                    }
                    
                    .download-popup {
                        background: white;
                        padding: 2rem;
                        border-radius: var(--border-radius);
                        box-shadow: var(--shadow-lg);
                        max-width: 500px;
                        width: 90%;
                        position: relative;
                    }
                    
                    .notify-form {
                        display: flex;
                        gap: 0.5rem;
                        margin-top: 1.5rem;
                    }
                    
                    .notify-form input {
                        flex: 1;
                        padding: 0.75rem;
                        border: 1px solid var(--border-color);
                        border-radius: var(--border-radius);
                    }
                    
                    .close-popup {
                        position: absolute;
                        top: 1rem;
                        right: 1rem;
                        background: none;
                        border: none;
                        font-size: 1.5rem;
                        cursor: pointer;
                        color: var(--text-light);
                    }
                    
                    @media (max-width: 576px) {
                        .notify-form {
                            flex-direction: column;
                        }
                    }
                `;
                document.head.appendChild(style);
                
                // Close popup functionality
                const closeButton = message.querySelector('.close-popup');
                closeButton.addEventListener('click', () => {
                    message.remove();
                });
                
                // Form submit handler
                const form = message.querySelector('.notify-form');
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const email = form.querySelector('input[type="email"]').value;
                    
                    // Replace form with thank you message
                    form.innerHTML = `<p class="success-message">Thank you! We'll notify you at ${email} when the app launches.</p>`;
                    
                    // Add success message style
                    const successStyle = document.createElement('style');
                    successStyle.textContent = `
                        .success-message {
                            color: var(--primary-color);
                            font-weight: 600;
                            padding: 1rem;
                            background-color: var(--bg-accent);
                            border-radius: var(--border-radius);
                            text-align: center;
                        }
                    `;
                    document.head.appendChild(successStyle);
                    
                    // Auto close after 3 seconds
                    setTimeout(() => {
                        message.remove();
                    }, 3000);
                });
            }
        });
    });
}); 