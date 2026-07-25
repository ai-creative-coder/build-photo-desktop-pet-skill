# Image provider selection and external adapter

## Contents

1. Provider decision
2. External provider contract
3. Configuration
4. Privacy and validation

## 1. Provider decision

Inside Codex, use the built-in `image_gen` tool by default. It needs no API key and remains the preferred path for the base character, turnaround and every state/key-pose generation or edit.

Outside Codex, or whenever the built-in tool is unavailable, stop before generation and tell the user that a separate image-generation model and API must be configured. Do not silently replace generation with placeholders, reuse another user's assets or claim that an external provider exists. Obtain explicit permission before uploading the user's photo or derived character to any external provider.

## 2. External provider contract

Use `scripts/external_image_provider.py` as the stable bridge. The user supplies a provider module outside the reusable Skill with this callable:

```python
def generate_image(*, request: dict, api_key: str, settings: dict) -> dict:
    # Call the selected provider's API.
    # Save final files locally.
    return {"outputs": ["/absolute/path/to/generated-image.png"], "provider": "name"}
```

The bridge deliberately does not assume one vendor's endpoint, multipart format or response schema. Provider-specific networking stays in the user's module.

The request JSON may include:

```json
{
  "operation": "generate",
  "prompt": "full production prompt",
  "reference_images": ["/absolute/path/to/current-user-reference.png"],
  "output_dir": "/absolute/path/to/project/output",
  "asset_name": "thinking-keypose-01"
}
```

For edits, use `"operation": "edit"` and list each image role explicitly. The provider must preserve reference-image order and return local output paths.

## 3. Configuration

Keep API keys only in environment variables:

```json
{
  "provider_file": "C:/path/to/my_image_provider.py",
  "entrypoint": "generate_image",
  "api_key_env": "MY_IMAGE_PROVIDER_API_KEY",
  "settings": {
    "endpoint": "https://provider.example/v1/images",
    "model": "configured-image-model"
  }
}
```

Validate the module without sending data:

```powershell
python <skill>\scripts\external_image_provider.py `
  --config <project>\external-image-provider.json `
  --check
```

Invoke only after user permission and local key configuration:

```powershell
python <skill>\scripts\external_image_provider.py `
  --config <project>\external-image-provider.json `
  --request <project>\image-request.json
```

## 4. Privacy and validation

- Never store an API key in the project, Skill, request JSON, logs or chat.
- State the selected provider/model and whether the current user's image will leave the machine.
- Do not send discarded variants, unrelated files or other users' data.
- Save provider outputs in the current user's private project and apply the same proportion, alpha, stability and final-release quality gates as built-in ImageGen output.
- An external provider does not waive any review gate. Reject its output when identity, anatomy, transparency, motion or continuity fails.
