document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const openBtn = document.getElementById('openSidebar');
    const closeBtn = document.getElementById('closeSidebar');
    const body = document.body;

    if (openBtn) {
        openBtn.addEventListener('click', () => {
            sidebar.classList.add('show');
            body.classList.add('sidebar-open');
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-open');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 768 && sidebar) {
            if (sidebar.classList.contains('show') && 
                !sidebar.contains(e.target) && 
                (!openBtn || !openBtn.contains(e.target))) {
                sidebar.classList.remove('show');
                body.classList.remove('sidebar-open');
            }
        }
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-open');
        }
    });
});
