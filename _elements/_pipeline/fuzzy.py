from fuzzywuzzy import process
import hashlib
import os


class FuzzyCache:
    def __init__(self):
        self.cache = {}

    def _hash_sentence(self, sentence):
        """Generate a hash for storage (optional, mainly for indexing)."""
        return hashlib.md5(sentence.encode()).hexdigest()

    def add(self, sentence, value):
        """Add a sentence and its corresponding value to the cache."""
        self.cache[sentence] = value

    def get(self, query, threshold=80):
        """Retrieve the most similar sentence with a similarity threshold."""
        if not self.cache:
            return None

        best_match, score = process.extractOne(query, self.cache.keys())
        if score >= threshold:
            return self.cache[best_match]
        return None  # No match found


cache = FuzzyCache()
current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.listdir(current_dir + "/content")
description = [
    "The forest is dense and lush, with heavy rain pouring down.",
    "Droplets bounce off the leaves, creating a misty atmosphere.",
    "The muddy path winds through the trees, slick with water, and small puddles form along the race track.",  # noqa
    "A confident rabbit stands on the path, grinning at the slow-moving turtle.",  # noqa
    "The rain drips down their fur and shell as they prepare to race.",
    "The rabbit, full of energy, dashes ahead, splashing water as it speeds through the muddy trail.",  # noqa
    "Meanwhile, the turtle moves steadily, unbothered by the rain.",
    "Midway through the race, the rabbit pauses under a large tree, yawning.",
    "Raindrops trickle down its fur as it leans against the trunk, deciding to take a quick nap.",  # noqa
    "The rain continues to fall, and the turtle slowly but persistently trudges through the wet path, leaving tiny footprints in the mud.",  # noqa
    "Suddenly, the rabbit wakes up and looks around.",
    "It spots the turtle nearing the finish line.",
    "In a panic, the rabbit sprints through the rain, mud splattering beneath its feet.",  # noqa
    "But it’s too late—the turtle crosses the finish line, smiling under the pouring rain.",  # noqa
    "The rabbit stops in disbelief, realizing that slow and steady has won the race." # noqa
]

for file in range(len(path)):
    with open(f"cache/{path[file]}", "r") as f:
        cache.add(description[file], f.read())
