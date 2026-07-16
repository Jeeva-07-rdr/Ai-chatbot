import os
import sys
from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = 'chat'

    def ready(self):
        # Display startup details inside Rich Panel and Table only when runserver launches
        if 'runserver' in sys.argv:
            if os.environ.get('RUN_MAIN') == 'true' or '--noreload' in sys.argv:
                try:
                    from django.conf import settings
                    from rich.console import Console
                    from rich.panel import Panel
                    from rich.table import Table

                    console = Console()

                    # Determine database backend
                    db_engine = settings.DATABASES['default']['ENGINE']
                    db_backend = "SQLite"
                    if 'mysql' in db_engine:
                        db_backend = "MySQL"
                    elif 'postgresql' in db_engine:
                        db_backend = "PostgreSQL"

                    # Default fallback parameters
                    provider = "Ollama (Local)"
                    theme = "Light Theme"
                    streaming = "Enabled"

                    # Retrieve database settings values dynamically
                    try:
                        from django.contrib.auth.models import User
                        from chat.models import UserSettings
                        user = User.objects.order_by('id').first()
                        if user:
                            user_settings = UserSettings.objects.filter(user=user).first()
                            if user_settings:
                                provider = user_settings.get_ai_provider_display()
                                theme = user_settings.get_theme_display()
                                streaming = "Enabled" if user_settings.streaming else "Disabled"
                    except Exception:
                        pass

                    # Render Startup Banner inside Panel
                    startup_panel = Panel(
                        "[bold cyan]UMI AI CHATBOT[/bold cyan]\n"
                        "[green]Django Server Started[/green]\n"
                        "Port: [yellow]8000[/yellow]",
                        title="[bold white]UMI Status[/bold white]",
                        border_style="cyan",
                        expand=False
                    )
                    console.print(startup_panel)

                    # Render Parameter Status Table
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Parameter", style="cyan", width=15)
                    table.add_column("Value", style="green", width=25)
                    
                    table.add_row("Provider", provider)
                    table.add_row("Database", db_backend)
                    table.add_row("Theme", theme)
                    table.add_row("Streaming", streaming)
                    table.add_row("Server", "Running")
                    
                    console.print(table)
                except Exception:
                    pass
