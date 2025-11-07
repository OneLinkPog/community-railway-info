# 🚄 Community Railway Info
A project for MrJulsen's Community Minecraft Server enabling users to view the status of any railway line quickly and conveniently.

# 🛠️ Setup
1. Clone the repository
2. Install the dependencies using `uv sync`
3. Copy the `config.example.yml` file to `config.yml` and fill in the required values
4. Create a `secret.key` file in the root directory and fill it with a random string. This will be used to encrypt the cookies.
   - You can generate a random string using `openssl rand -hex 32`
   - Alternatively, you can use `python3 -c 'import secrets; print(secrets.token_hex(32))'`
5. Run the server using `uv run __main__.py`