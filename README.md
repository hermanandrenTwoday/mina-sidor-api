# Mina Sidor API

Azure Functions API for the Mina Sidor integration with BEM.

## Repository layout

- `function_app.py` - HTTP-triggered Azure Functions.
- `database/` - SQL Server database project and schema material.
- `docs/` - Architecture and project documentation.
- `local.settings.sample.json` - Safe template for local application settings.

## Local development

Prerequisites:

- Python 3.13
- Azure Functions Core Tools v4
- Azurite (needed when local storage bindings are enabled)

Create and activate a virtual environment, then install dependencies:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create your local settings file from the template and fill in your own SQL Server connection string:

```powershell
Copy-Item local.settings.sample.json local.settings.json
```

`local.settings.json` contains secrets and is intentionally ignored by Git.

Start Azurite in one terminal, then run the Function host from another:

```powershell
azurite
func start
```

The current test endpoint expects a 12-digit person number:

```powershell
Invoke-RestMethod "http://localhost:7071/api/db-test?personnr=<12-digit-personnr>"
```

## Azure deployment

No automated deployment pipeline is configured yet. The intended workflow is:

1. Develop locally on a feature branch.
2. Push the branch and open a pull request.
3. Deploy the approved commit to the customer test environment through CI/CD.

Do not publish `local.settings.json` to Azure. Production settings, especially SQL connection strings, belong in Azure App Settings or Key Vault.
