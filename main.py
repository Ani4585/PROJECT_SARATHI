"""
PROJECT SARATHI

Application entry point.
"""

from config.settings import settings


def main():
    print("=" * 50)
    print(settings.APP_NAME)
    print("=" * 50)
    print(f"Version      : {settings.VERSION}")
    print(f"Environment  : {settings.ENVIRONMENT}")
    print(f"Project Root : {settings.PROJECT_ROOT}")
    print(f"Data Folder  : {settings.DATA_DIR}")
    print(f"Log Folder   : {settings.LOG_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()