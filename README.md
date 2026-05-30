# AI Data Analysis Agent

## Overview

AI Data Analysis Agent ek intelligent assistant hai jo SQLite databases, CSV files aur Excel files se data read karke natural language me answers provide karta hai. User simple English questions pooch sakta hai aur agent automatically data analyze karke insights, tables aur charts generate karta hai.

## Features

* SQLite Database Support
* CSV File Support
* Excel File Support (.xlsx, .xls)
* Natural Language Query Processing
* Automatic Data Analysis
* Chart Generation (Bar, Line, Pie, Scatter, etc.)
* Data Summarization
* Fast Query Execution
* AI-Powered Explanations

## Supported Data Sources

### SQLite

* Read tables from SQLite databases
* Execute generated SQL queries
* Retrieve structured data

### CSV Files

* Load and analyze CSV datasets
* Filter and aggregate data
* Generate insights

### Excel Files

* Read multiple sheets
* Analyze tabular data
* Create visual reports

## Example Queries

* What are the top 10 products by sales?
* Show monthly revenue trends.
* Which customer generated the highest revenue?
* Calculate average order value.
* Create a chart for yearly sales growth.
* Show data for the last 12 months.

## Project Structure

```text
project/
│
├── data/
│   ├── sample.csv
│   ├── sample.xlsx
│   └── database.db
│
├── agent/
│   ├── agent.py
│   ├── planner.py
│   ├── executor.py
│   └── charts.py
│
├── tests/
│
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone <repository-url>
cd project

pip install -r requirements.txt
```

## Usage

```python
result = agent.ask(
    "Show top 5 products by sales"
)

print(result["explanation"])
```

## Output Format

```python
{
    "success": True,
    "plan": {
        "source_type": "sqlite",
        "chart_type": "bar"
    },
    "data": dataframe,
    "explanation": "Top 5 products by sales are..."
}
```

## Technologies Used

* Python
* Pandas
* SQLite
* OpenPyXL
* Matplotlib
* Plotly
* NumPy
* AI/LLM Integration

## Future Enhancements

* PDF Data Extraction
* Real-Time Database Connections
* Dashboard Integration
* API Support
* Multi-Database Support
* Advanced Analytics

## License

This project is open-source and available for educational and research purposes.
