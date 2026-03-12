import os
from pathlib import Path

import schwab


def get_client():
    api_key = os.environ["SCHWAB_API_KEY"]
    secret = os.environ["SCHWAB_SECRET"]
    token_path = os.environ["SCHWAB_TOKEN_PATH"]
    callback_url = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

    if Path(token_path).exists():
        return schwab.auth.client_from_token_file(token_path, api_key, secret)

    print("No token file found. Starting first-time OAuth flow...")
    print(f"A browser window will open. After authorizing, you'll be redirected to {callback_url}")
    return schwab.auth.client_from_login_flow(api_key, secret, callback_url, token_path)
