from llm_tools import analyze_comp, all_comps


def main():
    user_input = input("Please Enter the company symbol to be analyzed: ")
    if (user_input not in all_comps.keys()):
        print(f"Please input correct company symbol")
        return

    result = analyze_comp(user_input)
    print(f"analysis saved in './data/{user_input}_analysis.md'")
    return result


if __name__ == "__main__":
    main()
