    

import argparse


def main():
    print("This is the CLI for the maths module.")
    parser = argparse.ArgumentParser(description="Maths module CLI")
    parser.add_argument(
        "--n", type=int, default=1, help="Number of questions to generate"
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Random seed for question generation"
    )
    parser.add_argument(
        "--topic", type=str, default="algebra", help="Topic for question generation"
    )
    parser.add_argument(
        "--difficulty", type=str, default="medium", help="Difficulty for question generation"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output questions in JSON format"
    )
    parser.print_help()


if __name__ == "__main__":    main()