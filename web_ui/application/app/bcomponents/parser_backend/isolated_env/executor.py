import json
import os

from workspace.parser import ParserImpl, PARSER_UID

batch = None
experiment = None
sample = None

parser = ParserImpl()

if os.path.exists("batch.json"):
    with open("batch.json", "r") as f:
        batch = json.loads(f.read())

        parser.process_batch(batch)
elif os.path.exists("experiment.json"):
    with open("experiment.json", "r") as f:
        experiment = json.loads(f.read())

        parser.process_experiment(batch)
elif os.path.exists("sample.json"):
    with open("sample.json", "r") as f:
        sample = json.loads(f.read())

        parser.process_experiment(batch)

for i, img in enumerate(parser.image_buffer):
    with open("output/%s_img_%i.%s" % (PARSER_UID, i, img["format"]), "wb") as f:
        f.write(img["image"])

with open("output/%s.txt" % PARSER_UID, "w") as f:
    f.write(parser.text_buffer)

