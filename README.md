# Rescue Quick (RQ) – A Smart Flood Rescue System

Severe flooding is a recurring crisis in the country, leaving countless individuals stranded and faced with the challenge of contacting the proper agencies for rescuing. Calling for rescue is often difficult due to different factors, such as network outages, overwhelming volumes of people loading emergency hotlines, and the desperate fight for survival.

This communication barrier often leaves the rescue team with the daunting task of locating and assisting an unknown number of people in flooded areas. Even when people can communicate successfully with the rescuers, vital information could be lost due to signals. Vital information such as location details often complicate rescue efforts, especially for areas with many streets and houses.

Currently, the country has no proper flood rescue system, which causes the citizens to seek help online or go to the highest place possible (e.g., their roofs) while hoping and praying that a rescuer will go to their area.

This leads to the creation of **Rescue Quick (RQ)**, an AI-powered flood monitoring and response system. The goals of the system are to help rescuers locate areas that need help/rescue and to identify other related information, such as the number of people, the type of people (e.g., mostly elderly, kids), etc.

## Development

### Python Dependencies
This project's Python dependencies are managed using [`uv`](https://github.com/astral-sh/uv). To install, please read the installation guide [here](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# Install/sync Python dependencies
uv sync
```

### Node Dependencies
Similarly, Node.js dependencies are managed using [`npm`](https://www.npmjs.com/). For installation instructions, read [this](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) (it is recommended to install this via [`nvm`](https://github.com/creationix/nvm)).

```bash
# Install Node dependencies
npm install
```

### Migrations

Before starting the application, make sure to run the necessary database migrations. 

```bash
# Runs database migrations
uv run manage.py migrate
```

### Development Server

For developing the application, a development server may be started which features automatic reloads.

```bash
# Starts a Django & Tailwind development server at `localhost:8000` by default
npm run dev
```

## Linting & Formatting

Before pushing a commit, you may want to run the [`ruff`](https://github.com/astral-sh/ruff) and [`djLint`](https://github.com/djlint/djLint) linters and formatters.

```bash
# ========== Ruff ==========
# Check linting
uv run ruff check

# Automatic fixing of simple linting errors
uv run ruff check --fix

# Check formatting
uv run ruff format --check

# Automatic reformatting
uv run ruff format

# ========== djLint ==========
# Check linting (for `html.j2` files)
uv run djlint . --extension=html.j2 --lint

# Check formatting (for `html.j2` files)
uv run djlint . --extension=html.j2 --check

# Automatic reformatting (for `html.j2` files)
uv run djlint . --extension=html.j2 --reformat
```

### Batching Linters & Formatters

You may also choose to batch linting/formatting commands using [`npm`].

```bash
# Check linting
npm run lint

# Automatic fixing of simple linting errors
npm run lint:fix

# Check formatting
npm run fmt

# Automatic reformatting
npm run fmt:fix
```
