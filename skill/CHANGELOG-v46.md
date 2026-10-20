# v46 — External systems → Specialized workflows

- Sessions that touch a system outside Microsoft 365 — a CRM or line-of-business app reached through a Power Platform connector or a third-party MCP server (e.g. Salesforce, Dynamics 365, ServiceNow, Jira, Workday, SAP, GitHub) — are classified as **Specialized workflows**.
- Order of the guiding rule: Email (final output is an email / inbox triage) → Communication (posts to Teams / mainly Teams synthesis) → **Specialized (outside-M365 system)** → code (skill build) → deliverable category.
- Detection: connector actions (InvokeConnectorOperation, HydrateConnector, CreateConnection), any MCP server not in the M365 set, non-M365 apps in `apps_accessed`, or goal text naming an external system.
