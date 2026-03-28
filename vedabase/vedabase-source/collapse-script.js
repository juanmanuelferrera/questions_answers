// Smart TOC collapse - only prevents navigation if item has children
(function() {
    'use strict';

    // Inject CSS to hide all nested ULs by default
    const style = document.createElement('style');
    style.id = 'toc-collapse-style';
    style.textContent = `
        /* Hide ALL nested ULs in TOC */
        #text-table-of-contents ul ul {
            display: none !important;
        }

        /* Show when parent LI has 'expanded' class */
        #text-table-of-contents li.expanded > ul {
            display: block !important;
        }

        /* Indicator styles */
        .toc-indicator {
            display: inline-block;
            margin-right: 5px;
            transition: transform 0.2s;
            color: #ea580c;
            font-weight: bold;
            cursor: pointer;
        }

        li.expanded > .toc-indicator {
            transform: rotate(90deg);
        }

        /* Make collapsible items obvious */
        #text-table-of-contents li:has(> ul) > a {
            cursor: pointer;
            font-weight: 500;
        }

        /* Active TOC link highlighting */
        #text-table-of-contents a.toc-active {
            background: #fed7aa;
            color: #9a3412;
            font-weight: 700;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
    `;

    if (document.head) {
        document.head.appendChild(style);
    }

    function collapseAll(parentLI) {
        // Recursively collapse this item and all descendants
        parentLI.classList.remove('expanded');

        // Find all descendant LIs and collapse them too
        const descendants = parentLI.querySelectorAll('li.expanded');
        descendants.forEach(li => li.classList.remove('expanded'));
    }

    function toggleItem(li, link, hasChildren) {
        // If no children, allow normal navigation
        if (!hasChildren) {
            return true; // Allow default navigation
        }

        const wasExpanded = li.classList.contains('expanded');

        if (wasExpanded) {
            // Collapse this item and all children
            collapseAll(li);
            console.log('✗ Collapsed:', link.textContent.trim().substring(0, 40));
        } else {
            // Expand this item (but keep children collapsed)
            li.classList.add('expanded');
            console.log('✓ Expanded:', link.textContent.trim().substring(0, 40));
        }

        return false; // Prevent default navigation
    }

    function setupTOC() {
        const toc = document.getElementById('text-table-of-contents');
        if (!toc) {
            console.log('TOC not found');
            return;
        }

        console.log('Setting up TOC collapse...');

        // Find ALL list items in the TOC
        const allLIs = toc.querySelectorAll('li');
        let setupCount = 0;

        allLIs.forEach((li) => {
            // Check if this LI has a direct child UL (making it collapsible)
            const hasNestedUL = li.querySelector(':scope > ul');

            // Get the link
            const link = li.querySelector(':scope > a');
            if (!link) return;

            // Skip if already setup
            if (li.dataset.tocSetup === 'true') return;
            li.dataset.tocSetup = 'true';

            // If has nested content, make it collapsible
            if (hasNestedUL) {
                setupCount++;

                // Add indicator if not present
                if (!li.querySelector('.toc-indicator')) {
                    const indicator = document.createElement('span');
                    indicator.className = 'toc-indicator';
                    indicator.textContent = '▶ ';
                    li.insertBefore(indicator, li.firstChild);
                }

                // Make link not navigate when it has children
                link.style.userSelect = 'none';

                // Add click handler that prevents navigation
                const clickHandler = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleItem(li, link, true);
                };

                // Remove old listeners by cloning
                const newLink = link.cloneNode(true);
                link.parentNode.replaceChild(newLink, link);
                newLink.addEventListener('click', clickHandler);

                const indicator = li.querySelector('.toc-indicator');
                if (indicator) {
                    const newIndicator = indicator.cloneNode(true);
                    indicator.parentNode.replaceChild(newIndicator, indicator);
                    newIndicator.addEventListener('click', clickHandler);
                }
            } else {
                // No nested content - allow normal navigation
                // Just ensure link works normally (no preventDefault)
                console.log('→ Normal link:', link.textContent.trim().substring(0, 40));
            }
        });

        console.log(`✓ Setup complete: ${setupCount} collapsible items`);
    }

    // Run setup multiple times
    function runSetup() {
        setupTOC();
        setTimeout(setupTOC, 100);
        setTimeout(setupTOC, 300);
        setTimeout(setupTOC, 500);
        setTimeout(setupTOC, 1000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runSetup);
    } else {
        runSetup();
    }
})();
