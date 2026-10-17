"""Run from any working directory: python /path/to/veilshard/main.py."""
import argparse
import os

def main():
    parser=argparse.ArgumentParser(description="Veilshard playable prototype")
    parser.add_argument("--headless",action="store_true",help="Use SDL dummy video/audio drivers")
    parser.add_argument("--frames",type=int,help="Exit after a bounded number of frames")
    args=parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"]="dummy"
        os.environ["SDL_AUDIODRIVER"]="dummy"
    from src.core.app import App
    App().run(args.frames)

if __name__=="__main__":
    main()
