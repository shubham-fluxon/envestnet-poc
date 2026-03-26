from strands.models.anthropic import AnthropicModel

# Shared Anthropic model for all agents.
# Reads ANTHROPIC_API_KEY from the environment automatically.
model = AnthropicModel(
    model_id="claude-sonnet-4-6",
    max_tokens=4096,
)
