import sys
import utils


def run():
    print(' '.join(utils.collect_sources(sys.argv[1:])))


if __name__ == '__main__':
    run()
