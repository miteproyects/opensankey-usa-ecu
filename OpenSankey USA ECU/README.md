# OpenSankey USA-ECU

Dual-country financial Sankey diagram visualization tool supporting both US Yahoo Finance data and Ecuadorian company financial data (NIIF-compliant).

## Features

- 🇺🇸 **US Mode**: Fetch live financial data from Yahoo Finance for any ticker symbol
- 🇪🇨 **Ecuador Mode**: View True Flavor S.A. (RUC 2390028132001) 2024 financial data in NIFF-compliant format
- Zero-crossing Sankey layout for clean visual flow
- Multiple themes and color palettes
- Export to HTML, PNG, SVG

## Running Locally

```bash
pip install streamlit plotly pandas yfinance kaleido
streamlit run sankey_app.py
```

## Data Sources

- **US**: Yahoo Finance (yfinance)
- **Ecuador**: Superintendencia de Compañías - True Flavor S.A. Financial Statements 2024

## About NIFF (Normas Internacionales de Información Financiera)

Ecuador adopted IFRS (NIIF in Spanish) for all companies. This app presents Ecuadorian financial data following:
- NIIF 1: First-time Adoption
- NIIF 15: Revenue from Contracts with Customers  
- NIIF 16: Leases
- NIC 1: Presentation of Financial Statements

## License

MIT
