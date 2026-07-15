# Setting up Antigravity CLI (agy) in CI/CD Pipelines

This guide describes how to configure, authenticate, and run the `agy` CLI in headless Continuous Integration (CI) environments (such as GitHub Actions).

---

## Authentication Model & Account Requirements

To authenticate and invoke Gemini models, the `agy` CLI communicates with the hosted Antigravity service using **Google User OAuth**. 

### Important Account Requirements
* **Google Workspace/User Account**: You **cannot** use a GCP Service Account (`.json` key file) directly, as the Antigravity service restricts access to verified user identities.
* **CI Bot/Service User**: For shared or production pipelines, it is recommended to create a dedicated Google Workspace user account (e.g., `a2ui-ci-bot@yourdomain.com`) that has been granted access to the Antigravity service.
* **API Keys**: While standard Python ADK-based agents can use a plain `GEMINI_API_KEY`, the compiled `agy` CLI requires its own session token to communicate with its backend workspace APIs.

---

## Step-by-Step CI Setup Flow

Because standard CI runners are headless and lack a web browser or keyring daemon, you must capture an authenticated session token locally and inject it into the pipeline.

### Step 1: Generate the Session Token via Podman/Docker

To simulate a clean, keyring-less environment and capture the file-based token:

1. Launch a temporary interactive container on your local machine:
   ```bash
   podman run -it --rm ubuntu:latest bash
   ```
2. Inside the container, install the requirements and the `agy` CLI:
   ```bash
   apt-get update && apt-get install -y curl
   curl -fsSL https://antigravity.google/cli/install.sh | bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
3. Initialize the authentication handshake by running any print command:
   ```bash
   agy -p "Hello"
   ```
4. Copy the OAuth URL printed in the terminal, log in using your browser with the designated Google/CI account, and authorize the permissions.
5. Paste the verification code back into the container terminal and press Enter.
6. Once the command completes successfully, print and copy the generated token payload:
   ```bash
   cat ~/.gemini/antigravity-cli/antigravity-oauth-token
   ```

### Step 2: Store the Token as a CI Secret

1. In your GitHub repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Create a new Repository Secret named:
   `AGY_AUTH_PROFILE_JSON`
3. Paste the entire content of the `antigravity-oauth-token` file you copied from Step 1.

---

## Step 3: Configure the GitHub Actions Workflow

In your workflow file (e.g. `.github/workflows/weekly_maintenance.yml`), add steps to recreate the config directory structure, write the token, pre-approve tool executions, and run `agy`.

Here is the recommended workflow configuration:

```yaml
      - name: Install Antigravity CLI
        run: |
          curl -fsSL https://antigravity.google/cli/install.sh | bash
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Authorize and Configure Antigravity CLI
        run: |
          # 1. Recreate the config directory structure
          mkdir -p ~/.gemini/antigravity-cli/

          # 2. Inject the persistent session token
          echo '${{ secrets.AGY_AUTH_PROFILE_JSON }}' > ~/.gemini/antigravity-cli/antigravity-oauth-token

          # 3. Create a permissive settings.json file to pre-approve tool actions
          # and prevent agy from prompting or hanging in headless mode.
          echo '{
            "permissions": {
              "allow": [
                "*"
              ]
            }
          }' > ~/.gemini/antigravity-cli/settings.json

      - name: Run Blueprint Compliance Audit Skill
        run: |
          # Wrap agy run in a python pty.spawn block to support terminal allocation
          # and pass the --dangerously-skip-permissions, --model, and --print-timeout flags.
          python3 -c "import os, pty, sys; status = pty.spawn(['agy', '--dangerously-skip-permissions', '--model', 'gemini-3.5-flash', '--print-timeout', '10m', '-p', '/a2ui-compliance Audit all codebase blueprints and post the compliance report issue.']); sys.exit(os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1)"
        env:
          GEMINI_API_KEY: ${{ secrets.REPO_GEMINI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Best Practices for Headless Execution

* **Always use `--dangerously-skip-permissions`**: This flag instructs the agent to auto-approve any tool-execution or file-modification permission prompts.
* **Secure the Token**: Treat the `AGY_AUTH_PROFILE_JSON` token with the same severity as a private API key, as it represents a persistent OAuth session. Rotate the session regularly or when the CI bot account's access needs to be revoked.
* **Control Permissions locally via settings.json**: If you need to restrict what shell commands the agent can run in the CI runner, narrow down the `"allow"` array in `settings.json` (e.g., allow only `"command(git)"` or specific test runner invocations).
