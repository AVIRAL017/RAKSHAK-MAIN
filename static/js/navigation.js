/**
 * RAKSHAK - Multi-page Navigation Router
 * Handles smooth transitions between pages with state management
 */

class SafeRouteNavigator {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.pageHistory = [this.currentPage];
        this.navigationState = {};
        this.loadingOverlay = null;
        
        this.init();
    }
    
    init() {
        this.createLoadingOverlay();
        this.setupEventListeners();
        this.updateActiveNavigation();
        this.loadPageState();
    }
    
    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/' || path === '') return 'home';
        return path.substring(1); // Remove leading slash
    }
    
    createLoadingOverlay() {
        this.loadingOverlay = document.createElement('div');
        this.loadingOverlay.id = 'pageLoadingOverlay';
        this.loadingOverlay.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-shield-alt fa-spin"></i>
                <p>Loading...</p>
            </div>
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            #pageLoadingOverlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(102, 126, 234, 0.95);
                backdrop-filter: blur(10px);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                transition: opacity 0.3s ease;
            }
            
            #pageLoadingOverlay.show {
                display: flex;
                opacity: 1;
            }
            
            .loading-spinner {
                text-align: center;
                color: white;
            }
            
            .loading-spinner i {
                font-size: 3rem;
                margin-bottom: 1rem;
                animation: spin 1s linear infinite;
            }
            
            .loading-spinner p {
                font-size: 1.2rem;
                font-weight: 500;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(this.loadingOverlay);
    }
    
    setupEventListeners() {
        // Handle navigation clicks
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('a[href^="/"], a[href^="#"]');
            if (navLink && this.shouldInterceptClick(navLink)) {
                e.preventDefault();
                const href = navLink.getAttribute('href');
                
                if (href.startsWith('#')) {
                    this.scrollToSection(href.substring(1));
                } else {
                    this.navigateTo(href, { transition: true });
                }
            }
        });
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (e) => {
            const page = this.getCurrentPage();
            if (e.state) {
                this.navigationState = e.state;
            }
            this.navigateTo(`/${page}`, { pushState: false, transition: true });
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshCurrentPage();
            }
        });
    }
    
    shouldInterceptClick(link) {
        // Don't intercept external links, downloads, or special links
        const href = link.getAttribute('href');
        return !link.hasAttribute('target') && 
               !link.hasAttribute('download') &&
               !href.includes('mailto:') &&
               !href.includes('tel:') &&
               !link.classList.contains('no-intercept');
    }
    
    async navigateTo(path, options = {}) {
        const {
            transition = true,
            pushState = true,
            data = {}
        } = options;
        
        try {
            if (transition) {
                this.showLoading();
            }
            
            // Update navigation state
            this.navigationState = { ...this.navigationState, ...data };
            
            // Simulate loading delay for smooth transition
            if (transition) {
                await new Promise(resolve => setTimeout(resolve, 300));
            }
            
            // Navigate to the new page
            if (pushState) {
                history.pushState(this.navigationState, '', path);
            }
            
            // Update current page
            const newPage = path === '/' ? 'home' : path.substring(1);
            this.currentPage = newPage;
            
            // Add to history
            if (pushState) {
                this.pageHistory.push(newPage);
                if (this.pageHistory.length > 10) {
                    this.pageHistory.shift(); // Keep only last 10 pages
                }
            }
            
            // Actually navigate
            window.location.href = path;
            
        } catch (error) {
            console.error('Navigation error:', error);
            this.hideLoading();
        }
    }
    
    showLoading() {
        this.loadingOverlay.classList.add('show');
    }
    
    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }
    
    updateActiveNavigation() {
        // Update active states in navigation menus
        const navLinks = document.querySelectorAll('.nav-menu a, .sidebar-nav a');
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            link.classList.remove('active');
            
            if (href === '/' && this.currentPage === 'home') {
                link.classList.add('active');
            } else if (href === `/${this.currentPage}`) {
                link.classList.add('active');
            }
        });
    }
    
    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
    
    goBack() {
        if (this.pageHistory.length > 1) {
            this.pageHistory.pop(); // Remove current page
            const previousPage = this.pageHistory[this.pageHistory.length - 1];
            const path = previousPage === 'home' ? '/' : `/${previousPage}`;
            this.navigateTo(path, { transition: true });
        } else {
            history.back();
        }
    }
    
    goForward() {
        history.forward();
    }
    
    refreshCurrentPage() {
        // Refresh current page data without full reload
        this.loadPageState();
    }
    
    savePageState(key, value) {
        this.navigationState[key] = value;
        history.replaceState(this.navigationState, '', window.location.pathname);
    }
    
    getPageState(key, defaultValue = null) {
        return this.navigationState[key] || defaultValue;
    }
    
    loadPageState() {
        // Load page-specific state and data
        const state = history.state;
        if (state) {
            this.navigationState = state;
        }
        
        // Emit page load event
        document.dispatchEvent(new CustomEvent('pageStateLoaded', {
            detail: { page: this.currentPage, state: this.navigationState }
        }));
    }
    
    // Public API methods
    static getInstance() {
        if (!SafeRouteNavigator.instance) {
            SafeRouteNavigator.instance = new SafeRouteNavigator();
        }
        return SafeRouteNavigator.instance;
    }
}

// Navigation Helper Functions
const navigation = {
    // Quick navigation methods
    goTo: (path, options = {}) => {
        SafeRouteNavigator.getInstance().navigateTo(path, options);
    },
    
    goBack: () => {
        SafeRouteNavigator.getInstance().goBack();
    },
    
    goForward: () => {
        SafeRouteNavigator.getInstance().goForward();
    },
    
    refresh: () => {
        SafeRouteNavigator.getInstance().refreshCurrentPage();
    },
    
    // State management
    saveState: (key, value) => {
        SafeRouteNavigator.getInstance().savePageState(key, value);
    },
    
    getState: (key, defaultValue) => {
        return SafeRouteNavigator.getInstance().getPageState(key, defaultValue);
    },
    
    // Page information
    getCurrentPage: () => {
        return SafeRouteNavigator.getInstance().currentPage;
    },
    
    getHistory: () => {
        return [...SafeRouteNavigator.getInstance().pageHistory];
    }
};

// Page Transition Effects
class PageTransitions {
    static fadeIn(element, duration = 300) {
        return new Promise(resolve => {
            element.style.opacity = '0';
            element.style.transition = `opacity ${duration}ms ease`;
            
            setTimeout(() => {
                element.style.opacity = '1';
                setTimeout(resolve, duration);
            }, 10);
        });
    }
    
    static slideIn(element, direction = 'right', duration = 300) {
        return new Promise(resolve => {
            const transform = direction === 'right' ? 'translateX(100%)' : 'translateX(-100%)';
            element.style.transform = transform;
            element.style.transition = `transform ${duration}ms ease`;
            
            setTimeout(() => {
                element.style.transform = 'translateX(0)';
                setTimeout(resolve, duration);
            }, 10);
        });
    }
    
    static scaleIn(element, duration = 300) {
        return new Promise(resolve => {
            element.style.transform = 'scale(0.95)';
            element.style.opacity = '0';
            element.style.transition = `all ${duration}ms ease`;
            
            setTimeout(() => {
                element.style.transform = 'scale(1)';
                element.style.opacity = '1';
                setTimeout(resolve, duration);
            }, 10);
        });
    }
}

// Initialize navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    SafeRouteNavigator.getInstance();
    
    // Add page transition effects to main content
    const mainContent = document.querySelector('main, .main-content');
    if (mainContent) {
        PageTransitions.fadeIn(mainContent);
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SafeRouteNavigator, navigation, PageTransitions };
} else {
    window.SafeRouteNavigator = SafeRouteNavigator;
    window.navigation = navigation;
    window.PageTransitions = PageTransitions;
}