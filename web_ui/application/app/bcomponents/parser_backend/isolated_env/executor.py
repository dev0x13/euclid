import json
import pickle
import os

from workspace.parser import ParserImpl, PARSER_UID

batch = None
experiment = None
sample = None

parser = ParserImpl()

if os.path.exists("workspace/batch.pkl"):
    with open("workspace/batch.pkl", "rb") as f:
        batch = pickle.load(f)

        parser.process_batch(batch)
elif os.path.exists("workspace/experiment.pkl"):
    with open("workspace/experiment.pkl", "rb") as f:
        experiment = pickle.load(f)

        parser.process_experiment(experiment)
elif os.path.exists("workspace/sample.pkl"):
    with open("workspace/sample.pkl", "rb") as f:
        sample = pickle.load(f)

        parser.process_experiment(sample)

for i, img in enumerate(parser.image_buffer):
    with open("output/%s_img_%i.%s" % (PARSER_UID, i, img["format"]), "wb") as f:
        f.write(img["image"])

with open("output/%s.txt" % PARSER_UID, "w") as f:
    f.write(parser.text_buffer)

