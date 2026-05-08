#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.
Enhanced version with environment detection and custom commands.
"""
import os
import sys
import platform
from pathlib import Path


def check_environment():
    """Check and display environment information"""
    print("=" * 60)
    print("Django Portfolio Management Utility")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Current Directory: {Path.cwd()}")

    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print(f"Virtual Environment: {sys.prefix}")
    else:
        print("⚠️  Warning: Not running in a virtual environment!")

    # Detect environment from ENVIRONMENT variable or --settings flag
    env = os.environ.get('ENVIRONMENT', 'development')
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings')

    print(f"Environment: {env}")
    print(f"Settings Module: {settings_module}")
    print("=" * 60)
    print()


def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = {
        'Django': 'django',
        'Pillow': 'PIL',
        'decouple': 'decouple',
        'crispy_forms': 'crispy_forms',
        'whitenoise': 'whitenoise',
    }

    missing = []
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package)

    if missing:
        print("⚠️  Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        print()
        return False

    return True


def setup_environment():
    """Setup environment variables from .env file"""
    try:
        from decouple import Config, RepositoryEnv
        from pathlib import Path

        env_path = Path(__file__).resolve().parent / '.env'

        if env_path.exists():
            # Load .env file using python-decouple
            config = Config(RepositoryEnv(str(env_path)))

            # Set critical environment variables
            if not os.environ.get('DJANGO_SETTINGS_MODULE'):
                env = config('ENVIRONMENT', default='development')
                os.environ.setdefault(
                    'DJANGO_SETTINGS_MODULE',
                    f'config.settings.{env}' if env != 'development' else 'config.settings'
                )

            if not os.environ.get('SECRET_KEY'):
                os.environ['SECRET_KEY'] = config('SECRET_KEY', default='dev-secret-key')

    except ImportError:
        # python-decouple not installed, use default settings
        pass
    except Exception as e:
        print(f"⚠️  Warning: Could not load .env file: {e}")


def main():
    """Run administrative tasks."""
    # Setup environment from .env file
    setup_environment()

    # Set default settings module if not already set
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    # Parse command line arguments for custom options
    if '--env' in sys.argv:
        env_index = sys.argv.index('--env')
        if env_index + 1 < len(sys.argv):
            env = sys.argv[env_index + 1]
            if env in ['development', 'production', 'testing']:
                os.environ['DJANGO_SETTINGS_MODULE'] = f'config.settings.{env}'
                # Remove custom args so Django doesn't choke
                sys.argv.pop(env_index + 1)
                sys.argv.pop(env_index)

    # Show environment info for certain commands
    show_info_commands = ['runserver', 'migrate', 'makemigrations', 'check']
    if any(cmd in sys.argv for cmd in show_info_commands):
        if '--quiet' not in sys.argv:
            check_environment()

    # Check dependencies before running critical commands
    critical_commands = ['migrate', 'runserver', 'collectstatic', 'test']
    if any(cmd in sys.argv for cmd in critical_commands):
        if '--skip-check' not in sys.argv:
            check_dependencies()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Execute the command
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()