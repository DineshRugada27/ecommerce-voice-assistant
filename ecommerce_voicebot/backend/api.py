
#This Python script creates a simple backend server using Flask that generates LiveKit access tokens.
#Front-end apps (web, mobile, AI agents, etc.) call this server to receive a token so they can join a LiveKit audio/video/AI room.

import os
import uuid #generate unique room names

from flask import Flask, request, jsonify
from flask_cors import CORS #allow requests from other origins (e.g., frontend app)
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants #LiveKit SDK classes for generating secure tokens

load_dotenv()

app = Flask(__name__)
CORS(app)


def generate_room():
    return "room-" + str(uuid.uuid4())[:8] #Creates a random room name like: room-a1b2c3d4


@app.route("/")
def health():
    return {"status": "LiveKit token server running ✅"} ##Visiting / returns a simple JSON response so you know the server is running.


@app.route("/getToken") #This endpoint is called by your frontend.
def get_token():
    name = request.args.get("name", "guest")
    room = request.args.get("room", generate_room()) 

    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        return jsonify({"error": "Missing LiveKit credentials"}), 500

    grants = VideoGrants(
        room_join=True,
        room=room,
    )

    token = (
        AccessToken(api_key, api_secret)
        .with_identity(name)
        .with_grants(grants)
        .to_jwt()
    )

    return jsonify({
        "token": token,
        "room": room,
        "identity": name
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False  # IMPORTANT on Windows
    )
