\# n8n Automation — Webhook to Field Transform



\## What I Built

A simple n8n workflow with two nodes:

1\. \*\*Webhook\*\* (trigger) — listens for POST requests on a unique URL

2\. \*\*Edit Fields\*\* (action) — receives the incoming data and adds a response\_message field



\## How I Tested It

1\. Used n8n's "Listen for test event" with the Test URL first, confirmed via curl:

&#x20;  curl -X POST http://localhost:5678/webhook-test/7f2ac930-639f-407d-a617-3de3be7d5ba6 -H "Content-Type: application/json" -d "{\\"message\\": \\"Hello from curl!\\"}"



2\. Published the workflow to make it live (Active), then tested the Production URL 

&#x20;  (no test button needed this time — confirms it works as a real integration point):

&#x20;  curl -X POST http://localhost:5678/webhook/7f2ac930-639f-407d-a617-3de3be7d5ba6 -H "Content-Type: application/json" -d "{\\"message\\": \\"Testing production webhook!\\"}"



Both returned: {"message":"Workflow was started"}



\## Key Takeaway

A webhook is just a URL that triggers a workflow when hit — any external system 

(a curl command, a FastAPI app, another server) can trigger automation this way 

without needing custom backend code for the "glue" logic. The difference between 

test URL and production URL is that production doesn't require manually clicking 

"listen" in the n8n editor — it's always on once published.

