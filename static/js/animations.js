/**
 * Portfolio - Animations
 * Version: 1.0
 */

// ===== GSAP Animations (requires GSAP library) =====
if (typeof gsap !== 'undefined') {

    // Register ScrollTrigger plugin
    if (typeof ScrollTrigger !== 'undefined') {
        gsap.registerPlugin(ScrollTrigger);
    }

    // ===== Page Load Animations =====
    function pageLoadAnimations() {
        const tl = gsap.timeline();

        tl.from('.navbar', {
            y: -100,
            opacity: 0,
            duration: 0.8,
            ease: 'power3.out'
        })
        .from('.hero-content h1', {
            y: 50,
            opacity: 0,
            duration: 0.8,
            ease: 'back.out(1.7)'
        }, '-=0.4')
        .from('.hero-content p', {
            y: 30,
            opacity: 0,
            duration: 0.6,
        }, '-=0.4')
        .from('.hero-buttons .btn', {
            y: 20,
            opacity: 0,
            duration: 0.5,
            stagger: 0.2,
        }, '-=0.3');
    }

    // ===== Scroll Animations =====
    function scrollAnimations() {
        // Fade up animations
        gsap.utils.toArray('.fade-up').forEach(element => {
            gsap.from(element, {
                scrollTrigger: {
                    trigger: element,
                    start: 'top 85%',
                    toggleActions: 'play none none none',
                },
                y: 60,
                opacity: 0,
                duration: 1,
                ease: 'power3.out',
            });
        });

        // Stagger animations for cards
        gsap.utils.toArray('.card-stagger').forEach(container => {
            gsap.from(container.children, {
                scrollTrigger: {
                    trigger: container,
                    start: 'top 80%',
                    toggleActions: 'play none none none',
                },
                y: 50,
                opacity: 0,
                duration: 0.6,
                stagger: 0.15,
                ease: 'back.out(1.2)',
            });
        });

        // Skill bars animation
        gsap.utils.toArray('.skill-progress').forEach(skill => {
            const progress = skill.querySelector('.progress-bar');
            if (progress) {
                gsap.from(progress, {
                    scrollTrigger: {
                        trigger: skill,
                        start: 'top 85%',
                        toggleActions: 'play none none none',
                    },
                    width: 0,
                    duration: 1.5,
                    ease: 'power2.out',
                });
            }
        });
    }

    // ===== Hover Animations =====
    function hoverAnimations() {
        // Card hover effect
        gsap.utils.toArray('.card-hover').forEach(card => {
            card.addEventListener('mouseenter', () => {
                gsap.to(card, {
                    y: -10,
                    scale: 1.02,
                    duration: 0.3,
                    ease: 'power2.out',
                });
            });

            card.addEventListener('mouseleave', () => {
                gsap.to(card, {
                    y: 0,
                    scale: 1,
                    duration: 0.3,
                    ease: 'power2.out',
                });
            });
        });

        // Social link hover
        gsap.utils.toArray('.social-link').forEach(link => {
            link.addEventListener('mouseenter', () => {
                gsap.to(link, {
                    y: -5,
                    scale: 1.1,
                    duration: 0.3,
                    ease: 'back.out(1.7)',
                });
            });

            link.addEventListener('mouseleave', () => {
                gsap.to(link, {
                    y: 0,
                    scale: 1,
                    duration: 0.3,
                    ease: 'power2.out',
                });
            });
        });
    }

    // ===== Parallax Effects =====
    function parallaxEffects() {
        gsap.utils.toArray('.parallax').forEach(element => {
            const speed = element.getAttribute('data-speed') || 0.5;

            gsap.to(element, {
                scrollTrigger: {
                    trigger: element,
                    start: 'top bottom',
                    end: 'bottom top',
                    scrub: true,
                },
                y: `${speed * 100}%`,
                ease: 'none',
            });
        });
    }

    // ===== Initialize =====
    document.addEventListener('DOMContentLoaded', () => {
        pageLoadAnimations();
        scrollAnimations();
        hoverAnimations();
        parallaxEffects();
    });
}

// ===== Particle Background (requires particles.js) =====
function initParticles() {
    if (typeof particlesJS !== 'undefined' && document.getElementById('particles-js')) {
        particlesJS('particles-js', {
            particles: {
                number: {
                    value: 80,
                    density: {
                        enable: true,
                        value_area: 800
                    }
                },
                color: {
                    value: '#2563eb'
                },
                shape: {
                    type: 'circle',
                },
                opacity: {
                    value: 0.5,
                    random: false,
                },
                size: {
                    value: 3,
                    random: true,
                },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: '#2563eb',
                    opacity: 0.4,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 2,
                    direction: 'none',
                    random: false,
                    straight: false,
                    out_mode: 'out',
                    bounce: false,
                }
            },
            interactivity: {
                detect_on: 'canvas',
                events: {
                    onhover: {
                        enable: true,
                        mode: 'grab'
                    },
                    onclick: {
                        enable: true,
                        mode: 'push'
                    },
                    resize: true
                },
                modes: {
                    grab: {
                        distance: 140,
                        line_linked: {
                            opacity: 1
                        }
                    },
                    push: {
                        particles_nb: 4
                    }
                }
            },
            retina_detect: true
        });
    }
}

// Initialize particles on load
document.addEventListener('DOMContentLoaded', initParticles);