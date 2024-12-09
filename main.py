from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument("-t", "--tags", type=str)
parser.add_argument("-s", "--save-dir", type=str)
parser.add_argument("-m", "--metadata", type=str, required=False, default="metadata.json")
args = parser.parse_args()



