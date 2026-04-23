import os

if __package__:
    from .app import create_app
else:
    from app import create_app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.environ.get("POULTRY_WEB_DEBUG", "0") == "1"
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
