# main.py
from src.agent import AstrologyAgent
from colorama import Fore, Style, init

# Initialize colors
init(autoreset=True)

def main():
    print(Fore.YELLOW + "=====================================================")
    print(Fore.YELLOW + "  PARAM-JYOTISHI: The AI Vedic Astrology Agent")
    print(Fore.YELLOW + "=====================================================")
    print(Style.DIM + "Initializing consciousness...\n")

    agent = AstrologyAgent()

    # Initial Trigger to set the persona
    # We send a blank message or a greeting to wake up the system instruction
    intro = agent.send_message("Hello, I am ready for a consultation.")
    print(Fore.CYAN + f"Param-Jyotishi: {intro}\n")

    while True:
        try:
            user_input = input(Fore.GREEN + "You: " + Style.RESET_ALL)

            if user_input.lower() in ['exit', 'quit', 'stop']:
                print(Fore.YELLOW + "Param-Jyotishi: Namaste. May the stars guide you.")
                break

            if user_input.strip() == "":
                continue

            print(Style.DIM + "(Contemplating charts...)\n")

            # Send to Agent
            response = agent.send_message(user_input)

            print(Fore.CYAN + "Param-Jyotishi:")
            print(Fore.WHITE + response + "\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
