import streamlit.web.cli as cli

cli.check_credentials = lambda: None

from streamlit.web.cli import main_run

if __name__ == "__main__":
    main_run()
