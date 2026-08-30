
@echo off
set ANTHROPIC_BASE_URL=https://daoxe.com
set ANTHROPIC_AUTH_TOKEN=sk-6nWjnXjd6q8YA4B7xl308oxmwh3G4JxNpzU0vXdlrxDpEDMd
set ANTHROPIC_MODEL=deepseek-chat
set ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-chat
set ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-chat
set ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-chat
set CLAUDE_CODE_SUBAGENT_MODEL=deepseek-chat
set CLAUDE_CODE_EFFORT_LEVEL=max
set CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432

npx @anthropic-ai/claude-code
pause
