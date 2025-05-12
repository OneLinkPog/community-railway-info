# 🚄 Community Railway Info
A project for MrJulsen's Community Minecraft Server enabling users to view the status of any railway line quickly and conveniently.

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

# 🛠️ Setup
1. Clone the repository
2. Install the dependencies using `pip install -r requirements.txt`
3. Copy the `config.example.yml` file to `config.yml` and fill in the required values
4. Create a `secret.key` file in the root directory and fill it with a random string. This will be used to encrypt the cookies.
   - You can generate a random string using `openssl rand -hex 32`
   - Alternatively, you can use `python3 -c 'import secrets; print(secrets.token_hex(32))'`
5. Run the server using `python3 __main__.py`