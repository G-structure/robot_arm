# Robot Arm Control Project

This project contains the software to control a robot arm, including a web-based UI for camera streaming and direct control.

## Project Structure

- `web_ui/`: Contains the Flask web application.
- `docs/`: Project documentation.
- `python_example/`: Original Python examples for controlling the arm.
- `notes/`: Scratchpad and development notes.
- `pyproject.toml`: Project definition and dependencies for `uv`.

## Getting Started

This project is managed with `uv`.

### Prerequisites

- Python 3.9+
- `uv` installed. See [official instructions](https://docs.astral.sh/uv/install.sh).

### Installation

Clone the repository and install the dependencies using `uv`:

```bash
uv sync
```

This will create a virtual environment in `.venv` and install all required packages.

### Running the Web UI

To start the web interface, run the following command from the project root:

```bash
uv run start-robot-ui
```

The application will be available at [http://localhost:5000](http://localhost:5000). 