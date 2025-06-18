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

## Command Line Options

The web UI supports the following command line arguments:

```bash
uv run start-robot-ui --help
```

### Available Arguments

- `--port PORT`: Specify the port to run the web server on (default: 5000)
- `--no-robot`: Disable robot connection for testing without a physical robot

### Examples

```bash
# Run on default port (5000)
uv run start-robot-ui

# Run on custom port
uv run start-robot-ui --port 8080

# Run without robot connection (for testing)
uv run start-robot-ui --no-robot

# Combine arguments
uv run start-robot-ui --port 3000 --no-robot
```

When using `--no-robot`, all robot commands will be simulated and the interface will show "Robot disabled (--no-robot mode)" in the status section. 