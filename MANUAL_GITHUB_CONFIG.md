# GitHub App Developer Console Configuration Matrix

Configure these exact settings in your GitHub App registration at https://github.com/settings/apps.

---

## General Settings

| Configuration Field | Target Setting / Production Value | Purpose in Your Architecture |
|---|---|---|
| **Homepage URL** | `https://mardi-cattle-charbroil.ngrok-free.dev` | Where users are sent to learn about your app. |
| **Callback URL** | `https://mardi-cattle-charbroil.ngrok-free.dev/auth/github/callback/` | Routes the `installation_id` to your Django `GitHubAppCallbackView`. |
| **Webhook URL** | `https://mardi-cattle-charbroil.ngrok-free.dev/webhooks/github` | Routes repository events to your Node.js ingestion gateway. |
| **Webhook Secret** | Your input key (e.g. `SuperSecretKey`) | Must match `process.env.GITHUB_WEBHOOK_SECRET` in `ingestion-service/index.js`. |

---

## Repository Permissions

| Permission | Setting | Purpose in Your Architecture |
|---|---|---|
| **Metadata** | Read-only | Automatically required by GitHub to track basic repository info. |
| **Contents** | Read & Write | Allows FastAPI `git_handler.py` to create branches and commit patched files for PRs. |
| **Pull Requests** | Read & Write | Allows your `EnterpriseGitHandler` to commit patches and open PRs. |
| **Commit statuses** | Read & Write | Allows the engine to display native green checkmarks in the PR via `GitHubStatusCheckManager`. |

---

## Subscribe to Events

| Event | Purpose |
|---|---|
| **Pull request** | Triggers your Node.js gateway on `opened` / `synchronize` actions. |
| **Issues** | Triggers your Node.js gateway on `opened` actions with fix keywords. |
| **Push** | Sends commit data for event filtration and pipeline triggering. |

---

## Where to Find These Settings

1. Go to **GitHub Settings** → **Developer settings** → **GitHub Apps**
2. Click **New GitHub App** or select your existing app
3. Fill in the **General** tab fields as shown above
4. Under **Permissions**, set Repository permissions to match the table
5. Under **Subscribe to events**, check **Pull request** and **Push**
6. Click **Save changes**
7. Copy the **App ID** and set it as `GITHUB_APP_IDENTIFIER` in your environment
8. Generate a **private key** (`.pem` file) and mount it at the path specified by `GITHUB_APP_PRIVATE_KEY_PATH`
9. Install the app on your organization and note the **Installation ID** stored by `GitHubAppCallbackView`
