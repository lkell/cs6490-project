import sys
from pathlib import Path
import pandas as pd
from plotnine import *

# Check for commandline args
if len(sys.argv) < 2:
  print("python visualize.py <sim_name>")
  exit(1)

# Get the input folder for csv objects
sim_name = sys.argv[1]
sim_path = (Path(__file__) / Path(f"../../output/{sim_name}/")).resolve()

# Create and clear the output folder for the image pdfs
output_path = (Path(__file__) / ".." / sim_name).resolve()
output_path.mkdir(exist_ok=True)
for file in output_path.glob("**/*.pdf"):
  file.unlink()


# Loop through the csv objects and load them in
pandas_csvs = {}
for file in sim_path.glob("**/*.csv"):
  node_name = str(file).split('/')[-1]
  pandas_csvs[node_name] = pd.read_csv(file)

queues = pd.concat(
  dict(filter(lambda val: "queue" in val[0], pandas_csvs.items()))
).reset_index()

queues.level_0 = queues.level_0.apply(lambda x: x.split("_")[0])

# Start plotting
plots = []

plots.append(ggplot(queues)
  + aes(x="time", y="queue_size")
  + geom_line()
  + facet_wrap('level_0')
  + labs(
    title="Queue Length Per Node",
    x="Time (Sim Seconds)",
    y="Queue Length",
    color="Node"
  ))

save_as_pdf_pages(plots,f"{output_path}/{sim_name}_vis.pdf")
