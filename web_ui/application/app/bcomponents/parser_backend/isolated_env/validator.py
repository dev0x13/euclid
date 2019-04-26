import inspect
import sys

try:
    from workspace.parser import Parser, ParserImpl
except ImportError:
    sys.exit("`ParserImpl` class is not found")
except Exception as e:
    sys.exit(str(e))

if not issubclass(ParserImpl, Parser):
    sys.exit("`ParserImpl` class should inherit `Parser`")

p = getattr(ParserImpl, "process_sample", None)
if not callable(p):
    sys.exit("missing `process_sample` method")
else:
    if "sample" not in inspect.getfullargspec(p)[0]:
        sys.exit("`process_sample` method missing `sample` argument")

p = getattr(ParserImpl, "process_experiment", None)
if not callable(p):
    sys.exit("missing `process_experiment` method")
else:
    if "experiment" not in inspect.getfullargspec(p)[0]:
        sys.exit("`process_experiment` method missing `experiment` argument")

p = getattr(ParserImpl, "process_batch", None)
if not callable(p):
    sys.exit("missing `process_batch` method")
else:
    if "batch" not in inspect.getfullargspec(p)[0]:
        sys.exit("`process_batch` method missing `batch` argument")

sys.exit()
