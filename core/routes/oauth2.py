from flask import Blueprint, session, redirect, url_for, request
from requests_oauthlib import OAuth2Session
from core.config import config
from core.url import *

auth = Blueprint('auth', __name__)


def token_updater(token):
    session['oauth2_token'] = token


def make_discord_session(token=None, state=None):
    return OAuth2Session(
        client_id=config.discord_client_id,
        token=token,
        state=state,
        redirect_uri=config.discord_redirect_uri,
        scope=['identify']
    )


@auth.route('/login')
async def login():
    discord = make_discord_session()
    authorization_url, state = discord.authorization_url(DISCORD_AUTH_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@auth.route('/callback')
async def callback():
    if request.values.get('error'):
        return request.values['error']

    discord = make_discord_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        DISCORD_TOKEN_URL,
        client_secret=config.discord_client_secret,
        authorization_response=request.url
    )

    session['oauth2_token'] = token

    discord = make_discord_session(token=token)
    user = discord.get(f'{DISCORD_API_URL}/users/@me').json()

    session['user'] = {
        'id': user['id'],
        'username': user['username'],
        'avatar': user['avatar'],
        "global_name": user.get('global_name', user['username']),
    }

    return redirect(url_for('index.index_route'))


@auth.route('/logout')
async def logout():
    session.clear()
    return redirect(url_for('index.index_route'))
