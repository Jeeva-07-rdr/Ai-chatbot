document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    const themeRadios = document.querySelectorAll('input[name="theme-options"]');

    // Check saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
        });
    }

    if (themeRadios) {
        themeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                if(e.target.id === 'themeDark') {
                    setTheme('dark');
                } else {
                    setTheme('light');
                }
            });
        });
    }

    function setTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update toggle icon
        if(themeToggle) {
            const icon = themeToggle.querySelector('i');
            if(theme === 'dark') {
                icon.classList.remove('bi-moon-stars');
                icon.classList.add('bi-sun');
            } else {
                icon.classList.remove('bi-sun');
                icon.classList.add('bi-moon-stars');
            }
        }

        // Update settings radio buttons if they exist
        const themeDarkInput = document.getElementById('themeDark');
        const themeLightInput = document.getElementById('themeLight');
        if (themeDarkInput && themeLightInput) {
            if(theme === 'dark') {
                themeDarkInput.checked = true;
            } else {
                themeLightInput.checked = true;
            }
        }
    }
});
