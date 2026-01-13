from cartesia import Cartesia

client = Cartesia(api_key="sk_car_52A7nZRcyQ6NZCKptwpHNo")
voices = client.voices.list()
for voice in voices:
    print(voice.id, voice.name)