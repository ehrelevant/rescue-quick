# Rescue Quick (RQ) – A Smart Flood Rescue System

Severe flooding is a recurring crisis in the country, leaving countless individuals stranded and faced with the challenge of contacting the proper agencies for rescuing. Calling for rescue is often difficult due to different factors, such as network outages, overwhelming volumes of people loading emergency hotlines, and the desperate fight for survival.

This communication barrier often leaves the rescue team with the daunting task of locating and assisting an unknown number of people in flooded areas. Even when people can communicate successfully with the rescuers, vital information could be lost due to signals. Vital information such as location details often complicate rescue efforts, especially for areas with many streets and houses.

Currently, the country has no proper flood rescue system, which causes the citizens to seek help online or go to the highest place possible (e.g., their roofs) while hoping and praying that a rescuer will go to their area.

This leads to the creation of **Rescue Quick (RQ)**, an AI-powered flood monitoring and response system. The goals of the system are to help rescuers locate areas that need help/rescue and to identify other related information, such as the number of people, the type of people (e.g., mostly elderly, kids), etc.

## Development

This project's dependencies are managed using [`uv`](https://github.com/astral-sh/uv). To install, please read the  installation guide [here](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# Install/sync dependencies
uv sync
```

For developing the application, a development server may be started which provides features such as automatic reloads.

```bash
# Starts a development server at `localhost:8000` by default
uv run manage.py runserver
```


## Linting & Formatting

Before pushing a commit, you may want to run the [`ruff`](https://github.com/astral-sh/ruff) linter and formatter.

```bash
# Runs linter (Ruff)
uv run ruff check

# Runs formatter (Ruff)
uv run ruff format
```
