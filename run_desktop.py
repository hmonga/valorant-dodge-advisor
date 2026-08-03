import argparse

from app.desktop import launch_desktop_app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Valorant Dodge Advisor")
    parser.add_argument("--overlay", action="store_true", help="Launch compact always-on-top companion window")
    args = parser.parse_args()
    launch_desktop_app(overlay=args.overlay)
