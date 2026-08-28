# Setting Up Claude Code with an API Key

## 1. Install Claude Code
If you haven't already, install the Claude Code CLI. On macOS/Linux you can run the official install script, or install via npm:

```bash
npm install -g @anthropic-ai/claude-code
```

## 2. Get an API key [OPTIONAL]
Go to [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys), sign in, and create a new key. Copy it right away — keys are shown only once. It will start with `sk-ant-`.

## 3. Set the ANTHROPIC_API_KEY environment variable
Add it to your shell config so it persists.

For **zsh** (default on macOS):
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc && source ~/.zshrc
```

For **bash**, use `~/.bash_profile` instead:
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bash_profile && source ~/.bash_profile
```

## 4. Launch Claude Code
Run `claude` in your terminal. Since it detects the `ANTHROPIC_API_KEY` variable, it will skip the browser login and instead ask you to approve using that key.

## 5. Verify the active auth method
Inside Claude Code, run `/status` at any time to confirm which authentication method is currently active and check that it's picking up the API key.
