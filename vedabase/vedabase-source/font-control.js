// Listen for messages from parent window to control font size and dark mode
(function() {
    'use strict';

    console.log('Font control script loaded in iframe');

    // Listen for messages from parent
    window.addEventListener('message', function(event) {
        console.log('Iframe received message:', event.data);

        if (event.data.type === 'setFontSize') {
            const fontSize = event.data.fontSize;
            console.log('Setting font size to:', fontSize);

            // Remove existing style
            let style = document.getElementById('custom-font-style');
            if (!style) {
                style = document.createElement('style');
                style.id = 'custom-font-style';
                document.head.appendChild(style);
            }

            style.textContent = `
                * {
                    font-size: ${fontSize}px !important;
                    line-height: 1.8 !important;
                }
            `;

            console.log('✓ Font size applied:', fontSize);
        }

        if (event.data.type === 'setDarkMode') {
            const isDark = event.data.isDark;
            console.log('Setting dark mode to:', isDark);

            // Remove existing style
            let style = document.getElementById('custom-dark-style');
            if (!style) {
                style = document.createElement('style');
                style.id = 'custom-dark-style';
                document.head.appendChild(style);
            }

            if (isDark) {
                style.textContent = `
                    body {
                        background: #000000 !important;
                    }
                    body, p, h1, h2, h3, h4, h5, h6, div, span, li, td, th, blockquote, pre, code, * {
                        color: #ffffff !important;
                    }
                    a {
                        color: #60a5fa !important;
                    }
                `;
                console.log('✓ Dark mode enabled');
            } else {
                style.textContent = '';
                console.log('✓ Dark mode disabled');
            }
        }
    });

    // Tell parent we're ready
    if (window.parent !== window) {
        window.parent.postMessage({ type: 'iframeReady' }, '*');
        console.log('Told parent iframe is ready');
    }
})();
