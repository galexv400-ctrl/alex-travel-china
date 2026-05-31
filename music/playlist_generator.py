import requests
import json
import time

API_KEY = "bf96d38ca8507198dc34add4caf049e4"
BASE_URL = "http://ws.audioscrobbler.com/2.0/"

BROADWAY_ARTISTS = [
    "Hadestown", "Waitress Musical", "Wicked", "Hamilton Musical",
    "Six the Musical", "Beetlejuice Musical", "Mean Girls Musical",
    "Legally Blonde Musical", "Mamma Mia", "Chicago Musical",
    "Kinky Boots Musical", "Anybody Can Dance", "Be More Chill Musical",
    "Fun Home Musical", "Come From Away"
]

POP_ARTISTS = [
    "Taylor Swift", "Lily Allen", "Lorde", "Dua Lipa", "Charli XCX",
    "Carly Rae Jepsen", "Katy Perry", "Robyn", "Chappell Roan", "Sabrina Carpenter"
]

RNB_ARTISTS = [
    "Kendrick Lamar", "Tyler the Creator", "Rosalia", "Drake",
    "Frank Ocean", "Jay-Z", "Beyonce", "TLC", "Destiny's Child",
    "Lauryn Hill", "Mary J. Blige", "Aaliyah", "SWV"
]

KNOWN_TRACKS = set([
    "wedding song", "back to hell", "spring", "wait for me",
    "come home with me", "tornado of opioids", "rainbow high",
    "everything's alright", "last midnight", "a little priest",
    "what is this feeling", "hey little songbird", "shake it off",
    "cruel summer", "not shy", "solar power", "bad guy",
    "smile", "the fear", "god save our young blood"
])

SAD_KEYWORDS = [
    "funeral", "death", "die", "dying", "goodbye forever", "farewell",
    "tragedy", "grief", "mourning", "weeping", "tears in", "broken heart",
    "i dreamed a dream", "on my own", "empty chairs", "bring him home",
    "who will love me as i am", "the last night of the world"
]


def get_similar_artists(artist_name):
    params = {
        "method": "artist.getSimilar",
        "artist": artist_name,
        "api_key": API_KEY,
        "format": "json",
        "limit": 5
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        data = r.json()
        if "similarartists" in data:
            return [a["name"] for a in data["similarartists"]["artist"]]
    except Exception:
        pass
    return []


def get_top_tracks(artist_name, limit=5):
    params = {
        "method": "artist.getTopTracks",
        "artist": artist_name,
        "api_key": API_KEY,
        "format": "json",
        "limit": limit
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        data = r.json()
        if "toptracks" in data:
            return [(t["name"], t["artist"]["name"]) for t in data["toptracks"]["track"]]
    except Exception:
        pass
    return []


def is_new_track(track_name):
    name = track_name.lower()
    if name in KNOWN_TRACKS:
        return False
    if any(sad in name for sad in SAD_KEYWORDS):
        return False
    return True


def build_playlist(seed_artists, label, mix_in_seeds=True):
    print(f"\nBuilding: {label}")
    playlist = []
    seen = set()

    # Add a few seed tracks from known artists
    if mix_in_seeds:
        for artist in seed_artists[:3]:
            tracks = get_top_tracks(artist, limit=2)
            for track, art in tracks:
                key = f"{track.lower()} - {art.lower()}"
                if key not in seen:
                    playlist.append((track, art, "favourite"))
                    seen.add(key)
            time.sleep(0.3)

    # Find similar artists and get their top tracks
    discovered_artists = set()
    for artist in seed_artists:
        similars = get_similar_artists(artist)
        for sim in similars:
            if sim not in seed_artists and sim not in discovered_artists:
                discovered_artists.add(sim)
        time.sleep(0.3)

    print(f"  Found {len(discovered_artists)} new artists to explore")

    for artist in list(discovered_artists)[:10]:
        tracks = get_top_tracks(artist, limit=3)
        for track, art in tracks:
            key = f"{track.lower()} - {art.lower()}"
            if key not in seen and is_new_track(track):
                playlist.append((track, art, "new discovery"))
                seen.add(key)
        time.sleep(0.3)

    return playlist


def save_playlist(playlist, filename, label):
    from collections import defaultdict
    by_artist = defaultdict(list)
    for track, artist, tag in playlist:
        by_artist[artist].append((track, tag))

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {label}\n")
        f.write(f"# {len(playlist)} tracks — grouped by artist to make adding easier\n")
        f.write("# Go to music.apple.com, create a new playlist, search each song and click +\n\n")
        i = 1
        for artist, tracks in sorted(by_artist.items()):
            f.write(f"\n--- {artist} ---\n")
            for track, tag in tracks:
                f.write(f"  {i}. {track}  [{tag}]\n")
                i += 1
    print(f"  Saved {len(playlist)} tracks to {filename}")


def main():
    print("Generating your summer playlists...\n")

    broadway = build_playlist(BROADWAY_ARTISTS, "Playlist 1: Broadway & Musicals")
    save_playlist(broadway, "playlist_1_broadway.txt", "Broadway & Musicals - Summer 2026")

    pop = build_playlist(POP_ARTISTS, "Playlist 2: Pop Favourites & Discoveries")
    save_playlist(pop, "playlist_2_pop.txt", "Pop Favourites & Discoveries - Summer 2026")

    rnb = build_playlist(RNB_ARTISTS, "Playlist 3: R&B & Hip-Hop")
    save_playlist(rnb, "playlist_3_rnb.txt", "R&B & Hip-Hop - Summer 2026")

    print("\nDone! Open the .txt files to see your playlists.")
    print("Search each song in Apple Music at music.apple.com and add to a new playlist.")


if __name__ == "__main__":
    main()
